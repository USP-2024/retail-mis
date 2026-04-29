import os
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, jsonify, request,
                   redirect, url_for, session, flash, send_file)
from werkzeug.utils import secure_filename

from config import DATA_PATH, UPLOAD_FOLDER, SECRET_KEY, USERS, REPORTS_DIR
from modules.data_importer   import DataImporter
from modules.data_cleaner    import DataCleaner
from modules.data_processor  import DataProcessor
from modules.analyzer        import Analyzer
from modules.rfm_analyzer    import RFMAnalyzer
from modules.recommender     import Recommender
from modules.visualizer      import Visualizer
from modules.report_generator import ReportGenerator
from modules.forecaster      import Forecaster
from modules.churn_predictor import ChurnPredictor
from modules.basket_analyzer import BasketAnalyzer
from modules.nlq_engine      import NLQEngine
from modules.pdf_generator   import PDFGenerator
from modules.db_manager      import DBManager
import modules.cache_manager as cache

app = Flask(__name__)
app.secret_key = SECRET_KEY
ALLOWED_EXTENSIONS = {"csv"}


# ── Auth decorators ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access required for this action.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Core data pipeline ───────────────────────────────────────────────────────
def run_pipeline(date_from=None, date_to=None):
    cache_key = f"pipeline_{date_from}_{date_to}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    importer = DataImporter(DATA_PATH)
    df = importer.load()
    importer.validate(df)
    df = DataCleaner().clean(df)
    processed_full = DataProcessor().process(df)

    # Apply date filter on cleaned df
    df_f = processed_full["df"].copy()
    if date_from:
        try:
            df_f = df_f[df_f["InvoiceDate"] >= datetime.strptime(date_from, "%Y-%m-%d")]
        except Exception:
            pass
    if date_to:
        try:
            df_f = df_f[df_f["InvoiceDate"] <= datetime.strptime(date_to, "%Y-%m-%d")]
        except Exception:
            pass

    processed = DataProcessor().process(df_f)
    insights  = Analyzer().analyze(processed)

    rfm_df      = RFMAnalyzer().compute(df_f)
    rfm_summary = RFMAnalyzer().segment_summary(rfm_df)
    recs        = Recommender().generate(insights, rfm_df)

    # Forecast
    monthly_dict = dict(zip(insights["monthly_labels"], insights["monthly_revenues"]))
    forecast     = Forecaster().forecast(monthly_dict, periods=3)

    # Churn prediction
    churn_df = ChurnPredictor().predict(rfm_df)

    # Market basket
    basket = BasketAnalyzer().analyze(df_f, top_n=10)

    Visualizer().plot(insights)
    report_paths = ReportGenerator().generate(insights, rfm_df, recs)

    db = DBManager()
    db.save(df_f, "transactions")
    db.save(rfm_df, "rfm")

    result = {
        "insights":        insights,
        "rfm_summary":     rfm_summary.to_dict(orient="records"),
        "recommendations": recs,
        "report_paths":    report_paths,
        "forecast":        forecast,
        "churn_df":        churn_df.to_dict(orient="records"),
        "basket":          basket,
        "processed":       processed,
        "processed_full":  processed_full,
        "rfm_df":          rfm_df,
    }
    cache.set(cache_key, result)
    return result


# ── Auth routes ──────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = USERS.get(username)
        if user and user["password"] == password:
            session["user"] = username
            session["role"] = user["role"]
            flash(f"Welcome back, {username.capitalize()}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


# ── Main routes ──────────────────────────────────────────────────────────────
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    date_from = request.args.get("date_from", "")
    date_to   = request.args.get("date_to",   "")
    data = run_pipeline(date_from=date_from or None, date_to=date_to or None)
    ins  = data["insights"]
    fc   = data["forecast"]

    # Merge actual + forecast for chart
    all_labels    = ins["monthly_labels"] + fc["forecast_labels"]
    all_revenues  = ins["monthly_revenues"] + [None] * len(fc["forecast_labels"])
    fc_vals       = [None] * len(ins["monthly_labels"]) + fc["forecast_values"]
    upper_vals    = [None] * len(ins["monthly_labels"]) + fc["upper"]
    lower_vals    = [None] * len(ins["monthly_labels"]) + fc["lower"]

    return render_template(
        "dashboard.html",
        insights           = ins,
        rfm_summary        = data["rfm_summary"],
        recommendations    = data["recommendations"],
        report_paths       = data["report_paths"],
        forecast           = fc,
        churn_data         = data["churn_df"],
        churn_lookup       = {str(c["CustomerID"]): c for c in data["churn_df"]},
        basket             = data["basket"],
        date_from          = date_from,
        date_to            = date_to,
        role               = session.get("role"),
        username           = session.get("user"),
        all_labels         = all_labels,
        all_revenues       = all_revenues,
        forecast_vals      = fc_vals,
        upper_vals         = upper_vals,
        lower_vals         = lower_vals,
        top_product_labels = [p["Description"] for p in ins["top_products"][:8]],
        top_product_revenues=[round(p["Revenue"],2) for p in ins["top_products"][:8]],
        country_labels     = [c["Country"] for c in ins["top_countries"]],
        country_revenues   = [round(c["Revenue"],2) for c in ins["top_countries"]],
        rfm_labels         = [r["Segment"] for r in data["rfm_summary"]],
        rfm_counts         = [r["Count"] for r in data["rfm_summary"]],
        heatmap_dow        = ins.get("heatmap_dow", {}),
        heatmap_month      = ins.get("heatmap_month", {}),
    )

@app.route("/report")
@login_required
def report():
    data = run_pipeline()
    return render_template(
        "report.html",
        insights      = data["insights"],
        top_products  = data["insights"]["top_products"],
        top_customers = data["insights"]["top_customers"],
        top_countries = data["insights"]["top_countries"],
        rfm_summary   = data["rfm_summary"],
        report_paths  = data["report_paths"],
        role          = session.get("role"),
        username      = session.get("user"),
    )

@app.route("/customer/<customer_id>")
@login_required
def customer_detail(customer_id):
    data = run_pipeline()
    # Use full processed data — same pipeline run as dashboard
    df   = data["processed_full"]["df"]
    cust = df[df["CustomerID"] == str(customer_id)]
    if cust.empty:
        # Fallback: try the filtered processed data
        df   = data["processed"]["df"]
        cust = df[df["CustomerID"] == str(customer_id)]
    if cust.empty:
        flash(f"Customer {customer_id} not found. Try refreshing the cache.", "warning")
        return redirect(url_for("dashboard"))

    orders = (
        cust.groupby("InvoiceNo")
        .agg(Date=("InvoiceDate","max"), Items=("Quantity","sum"),
             Revenue=("Revenue","sum"), Products=("Description","nunique"))
        .sort_values("Date", ascending=False)
        .head(20).reset_index()
    )
    orders["Date"]     = orders["Date"].dt.strftime("%d %b %Y")
    orders["Items"]    = orders["Items"].astype(int)
    orders["Products"] = orders["Products"].astype(int)
    orders["Revenue"]  = orders["Revenue"].round(2).astype(float)

    top_prods = (
        cust.groupby("Description")["Revenue"].sum()
        .sort_values(ascending=False).head(5).reset_index()
    )

    rfm_row  = data["rfm_df"][data["rfm_df"]["CustomerID"] == str(customer_id)]
    if not rfm_row.empty:
        raw = rfm_row.iloc[0].to_dict()
        rfm_data = {
            k: (round(float(v), 2) if hasattr(v, '__float__') and not isinstance(v, str)
                else (int(v) if hasattr(v, '__int__') and not isinstance(v, (str, float, bool))
                      else str(v) if hasattr(v, 'item') else v))
            for k, v in raw.items()
        }
    else:
        rfm_data = {}
    churn_row = next((c for c in data["churn_df"] if str(c["CustomerID"]) == str(customer_id)), {})

    segment  = rfm_data.get("Segment", "Unknown")
    rec_map  = {
        "Champions":           "Reward with exclusive offers and early product access.",
        "Loyal Customers":     "Offer a loyalty programme or referral incentives.",
        "Potential Loyalists": "Engage with personalised email campaigns.",
        "At Risk":             "Send a win-back campaign with a special discount code.",
        "Lost":                "Attempt re-engagement with a strong time-limited incentive.",
    }
    cust_rec = rec_map.get(segment, "Monitor behaviour and engage proactively.")

    return render_template(
        "customer.html",
        customer_id   = customer_id,
        orders        = orders.to_dict(orient="records"),
        top_products  = top_prods.to_dict(orient="records"),
        rfm           = rfm_data,
        churn         = churn_row,
        recommendation= cust_rec,
        total_revenue = round(float(cust["Revenue"].sum()), 2),
        total_orders  = int(cust["InvoiceNo"].nunique()),
        first_purchase= cust["InvoiceDate"].min().strftime("%d %b %Y"),
        last_purchase = cust["InvoiceDate"].max().strftime("%d %b %Y"),
        role          = session.get("role"),
        username      = session.get("user"),
    )

@app.route("/upload", methods=["GET", "POST"])
@admin_required
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in request.", "danger")
            return redirect(request.url)
        f = request.files["file"]
        if not f or f.filename == "":
            flash("No file selected.", "danger")
            return redirect(request.url)
        if allowed_file(f.filename):
            f.save(os.path.join(UPLOAD_FOLDER, "retail.csv"))
            cache.clear()
            flash("Dataset uploaded! Dashboard refreshed with new data.", "success")
            return redirect(url_for("dashboard"))
        flash("Only CSV files are accepted.", "danger")
    return render_template("upload.html",
                           role=session.get("role"),
                           username=session.get("user"))


# ── API routes ───────────────────────────────────────────────────────────────
@app.route("/api/nlq", methods=["POST"])
@login_required
def nlq():
    question = (request.json or {}).get("question", "")
    if not question.strip():
        return jsonify({"answer": "Please type a question."})
    try:
        data   = run_pipeline()
        engine = NLQEngine(data["processed_full"], data["insights"], data["rfm_df"])
        return jsonify({"answer": engine.query(question)})
    except Exception as e:
        return jsonify({"answer": f"Sorry, I encountered an error: {e}"})

@app.route("/api/refresh")
@admin_required
def refresh():
    cache.clear()
    flash("Cache cleared. Data refreshed.", "success")
    return redirect(url_for("dashboard"))

@app.route("/api/download/pdf")
@login_required
def download_pdf():
    try:
        data = run_pipeline()
        path = PDFGenerator().generate(
            data["insights"], data["rfm_summary"], data["recommendations"])
        return send_file(path, as_attachment=True, download_name="RetailMIS_Report.pdf")
    except Exception as e:
        flash(f"PDF generation failed: {e}", "danger")
        return redirect(url_for("report"))


@app.route("/charttest")
def charttest():
    return render_template("charttest.html")

if __name__ == "__main__":
    app.run(debug=True)
# import os
# from datetime import datetime
# from functools import wraps

# from flask import (Flask, render_template, jsonify, request,
#                    redirect, url_for, session, flash, send_file)
# from werkzeug.utils import secure_filename

# from config import DATA_PATH, UPLOAD_FOLDER, SECRET_KEY, USERS, REPORTS_DIR
# from modules.data_importer   import DataImporter
# from modules.data_cleaner    import DataCleaner
# from modules.data_processor  import DataProcessor
# from modules.analyzer        import Analyzer
# from modules.rfm_analyzer    import RFMAnalyzer
# from modules.recommender     import Recommender
# from modules.visualizer      import Visualizer
# from modules.report_generator import ReportGenerator
# from modules.forecaster      import Forecaster
# from modules.churn_predictor import ChurnPredictor
# from modules.basket_analyzer import BasketAnalyzer
# from modules.nlq_engine      import NLQEngine
# from modules.pdf_generator   import PDFGenerator
# from modules.db_manager      import DBManager
# import modules.cache_manager as cache

# app = Flask(__name__)
# app.secret_key = SECRET_KEY
# ALLOWED_EXTENSIONS = {"csv"}


# # ── Auth decorators ──────────────────────────────────────────────────────────
# def login_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         if "user" not in session:
#             flash("Please log in to access this page.", "warning")
#             return redirect(url_for("login"))
#         return f(*args, **kwargs)
#     return decorated

# def admin_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         if "user" not in session:
#             return redirect(url_for("login"))
#         if session.get("role") != "admin":
#             flash("Admin access required for this action.", "danger")
#             return redirect(url_for("dashboard"))
#         return f(*args, **kwargs)
#     return decorated

# def allowed_file(filename):
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# # ── Core data pipeline ───────────────────────────────────────────────────────
# def run_pipeline(date_from=None, date_to=None):
#     cache_key = f"pipeline_{date_from}_{date_to}"
#     cached = cache.get(cache_key)
#     if cached:
#         return cached

#     importer = DataImporter(DATA_PATH)
#     df = importer.load()
#     importer.validate(df)
#     df = DataCleaner().clean(df)
#     processed_full = DataProcessor().process(df)

#     # Apply date filter on cleaned df
#     df_f = processed_full["df"].copy()
#     if date_from:
#         try:
#             df_f = df_f[df_f["InvoiceDate"] >= datetime.strptime(date_from, "%Y-%m-%d")]
#         except Exception:
#             pass
#     if date_to:
#         try:
#             df_f = df_f[df_f["InvoiceDate"] <= datetime.strptime(date_to, "%Y-%m-%d")]
#         except Exception:
#             pass

#     processed = DataProcessor().process(df_f)
#     insights  = Analyzer().analyze(processed)

#     rfm_df      = RFMAnalyzer().compute(df_f)
#     rfm_summary = RFMAnalyzer().segment_summary(rfm_df)
#     recs        = Recommender().generate(insights, rfm_df)

#     # Forecast
#     monthly_dict = dict(zip(insights["monthly_labels"], insights["monthly_revenues"]))
#     forecast     = Forecaster().forecast(monthly_dict, periods=3)

#     # Churn prediction
#     churn_df = ChurnPredictor().predict(rfm_df)

#     # Market basket
#     basket = BasketAnalyzer().analyze(df_f, top_n=10)

#     Visualizer().plot(insights)
#     report_paths = ReportGenerator().generate(insights, rfm_df, recs)

#     db = DBManager()
#     db.save(df_f, "transactions")
#     db.save(rfm_df, "rfm")

#     result = {
#         "insights":        insights,
#         "rfm_summary":     rfm_summary.to_dict(orient="records"),
#         "recommendations": recs,
#         "report_paths":    report_paths,
#         "forecast":        forecast,
#         "churn_df":        churn_df.head(20).to_dict(orient="records"),
#         "basket":          basket,
#         "processed":       processed,
#         "rfm_df":          rfm_df,
#     }
#     cache.set(cache_key, result)
#     return result


# # ── Auth routes ──────────────────────────────────────────────────────────────
# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if "user" in session:
#         return redirect(url_for("dashboard"))
#     if request.method == "POST":
#         username = request.form.get("username", "").strip()
#         password = request.form.get("password", "")
#         user = USERS.get(username)
#         if user and user["password"] == password:
#             session["user"] = username
#             session["role"] = user["role"]
#             flash(f"Welcome back, {username.capitalize()}!", "success")
#             return redirect(url_for("dashboard"))
#         flash("Invalid username or password.", "danger")
#     return render_template("login.html")

# @app.route("/logout")
# def logout():
#     session.clear()
#     flash("You have been logged out successfully.", "info")
#     return redirect(url_for("login"))


# # ── Main routes ──────────────────────────────────────────────────────────────
# @app.route("/")
# def home():
#     if "user" not in session:
#         return redirect(url_for("login"))
#     return redirect(url_for("dashboard"))

# @app.route("/dashboard")
# @login_required
# def dashboard():
#     date_from = request.args.get("date_from", "")
#     date_to   = request.args.get("date_to",   "")
#     data = run_pipeline(date_from=date_from or None, date_to=date_to or None)
#     ins  = data["insights"]
#     fc   = data["forecast"]

#     # Merge actual + forecast for chart
#     all_labels    = ins["monthly_labels"] + fc["forecast_labels"]
#     all_revenues  = ins["monthly_revenues"] + [None] * len(fc["forecast_labels"])
#     fc_vals       = [None] * len(ins["monthly_labels"]) + fc["forecast_values"]
#     upper_vals    = [None] * len(ins["monthly_labels"]) + fc["upper"]
#     lower_vals    = [None] * len(ins["monthly_labels"]) + fc["lower"]

#     return render_template(
#         "dashboard.html",
#         insights           = ins,
#         rfm_summary        = data["rfm_summary"],
#         recommendations    = data["recommendations"],
#         report_paths       = data["report_paths"],
#         forecast           = fc,
#         churn_data         = data["churn_df"],
#         basket             = data["basket"],
#         date_from          = date_from,
#         date_to            = date_to,
#         role               = session.get("role"),
#         username           = session.get("user"),
#         all_labels         = all_labels,
#         all_revenues       = all_revenues,
#         forecast_vals      = fc_vals,
#         upper_vals         = upper_vals,
#         lower_vals         = lower_vals,
#         top_product_labels = [p["Description"] for p in ins["top_products"][:8]],
#         top_product_revenues=[round(p["Revenue"],2) for p in ins["top_products"][:8]],
#         country_labels     = [c["Country"] for c in ins["top_countries"]],
#         country_revenues   = [round(c["Revenue"],2) for c in ins["top_countries"]],
#         rfm_labels         = [r["Segment"] for r in data["rfm_summary"]],
#         rfm_counts         = [r["Count"] for r in data["rfm_summary"]],
#         heatmap_dow        = ins.get("heatmap_dow", {}),
#         heatmap_month      = ins.get("heatmap_month", {}),
#     )

# @app.route("/report")
# @login_required
# def report():
#     data = run_pipeline()
#     return render_template(
#         "report.html",
#         insights      = data["insights"],
#         top_products  = data["insights"]["top_products"],
#         top_customers = data["insights"]["top_customers"],
#         top_countries = data["insights"]["top_countries"],
#         rfm_summary   = data["rfm_summary"],
#         report_paths  = data["report_paths"],
#         role          = session.get("role"),
#         username      = session.get("user"),
#     )

# @app.route("/customer/<customer_id>")
# @login_required
# def customer_detail(customer_id):
#     data = run_pipeline()
#     df   = data["processed"]["df"]
#     cust = df[df["CustomerID"] == str(customer_id)]
#     if cust.empty:
#         flash(f"Customer {customer_id} not found.", "warning")
#         return redirect(url_for("dashboard"))

#     orders = (
#         cust.groupby("InvoiceNo")
#         .agg(Date=("InvoiceDate","max"), Items=("Quantity","sum"),
#              Revenue=("Revenue","sum"), Products=("Description","nunique"))
#         .sort_values("Date", ascending=False)
#         .head(20).reset_index()
#     )
#     orders["Date"] = orders["Date"].dt.strftime("%d %b %Y")

#     top_prods = (
#         cust.groupby("Description")["Revenue"].sum()
#         .sort_values(ascending=False).head(5).reset_index()
#     )

#     rfm_row  = data["rfm_df"][data["rfm_df"]["CustomerID"] == str(customer_id)]
#     rfm_data = rfm_row.iloc[0].to_dict() if not rfm_row.empty else {}
#     churn_row= next((c for c in data["churn_df"] if str(c["CustomerID"]) == str(customer_id)), {})

#     segment  = rfm_data.get("Segment", "Unknown")
#     rec_map  = {
#         "Champions":           "Reward with exclusive offers and early product access.",
#         "Loyal Customers":     "Offer a loyalty programme or referral incentives.",
#         "Potential Loyalists": "Engage with personalised email campaigns.",
#         "At Risk":             "Send a win-back campaign with a special discount code.",
#         "Lost":                "Attempt re-engagement with a strong time-limited incentive.",
#     }
#     cust_rec = rec_map.get(segment, "Monitor behaviour and engage proactively.")

#     return render_template(
#         "customer.html",
#         customer_id   = customer_id,
#         orders        = orders.to_dict(orient="records"),
#         top_products  = top_prods.to_dict(orient="records"),
#         rfm           = rfm_data,
#         churn         = churn_row,
#         recommendation= cust_rec,
#         total_revenue = round(cust["Revenue"].sum(), 2),
#         total_orders  = cust["InvoiceNo"].nunique(),
#         first_purchase= cust["InvoiceDate"].min().strftime("%d %b %Y"),
#         last_purchase = cust["InvoiceDate"].max().strftime("%d %b %Y"),
#         role          = session.get("role"),
#         username      = session.get("user"),
#     )

# @app.route("/upload", methods=["GET", "POST"])
# @admin_required
# def upload():
#     if request.method == "POST":
#         if "file" not in request.files:
#             flash("No file part in request.", "danger")
#             return redirect(request.url)
#         f = request.files["file"]
#         if not f or f.filename == "":
#             flash("No file selected.", "danger")
#             return redirect(request.url)
#         if allowed_file(f.filename):
#             f.save(os.path.join(UPLOAD_FOLDER, "retail.csv"))
#             cache.clear()
#             flash("Dataset uploaded! Dashboard refreshed with new data.", "success")
#             return redirect(url_for("dashboard"))
#         flash("Only CSV files are accepted.", "danger")
#     return render_template("upload.html",
#                            role=session.get("role"),
#                            username=session.get("user"))


# # ── API routes ───────────────────────────────────────────────────────────────
# @app.route("/api/nlq", methods=["POST"])
# @login_required
# def nlq():
#     question = (request.json or {}).get("question", "")
#     if not question.strip():
#         return jsonify({"answer": "Please type a question."})
#     try:
#         data   = run_pipeline()
#         engine = NLQEngine(data["processed"], data["insights"], data["rfm_df"])
#         return jsonify({"answer": engine.query(question)})
#     except Exception as e:
#         return jsonify({"answer": f"Sorry, I encountered an error: {e}"})

# @app.route("/api/refresh")
# @admin_required
# def refresh():
#     cache.clear()
#     flash("Cache cleared. Data refreshed.", "success")
#     return redirect(url_for("dashboard"))

# @app.route("/api/download/pdf")
# @login_required
# def download_pdf():
#     try:
#         data = run_pipeline()
#         path = PDFGenerator().generate(
#             data["insights"], data["rfm_summary"], data["recommendations"])
#         return send_file(path, as_attachment=True, download_name="RetailMIS_Report.pdf")
#     except Exception as e:
#         flash(f"PDF generation failed: {e}", "danger")
#         return redirect(url_for("report"))


# @app.route("/charttest")
# def charttest():
#     return render_template("charttest.html")

# if __name__ == "__main__":
#     app.run(debug=True)