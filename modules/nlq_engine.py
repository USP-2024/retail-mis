import re
from utils.logger import log

MONTHS = {
    "january": 1,  "february": 2, "march": 3,    "april": 4,
    "may": 5,      "june": 6,     "july": 7,      "august": 8,
    "september": 9,"october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

class NLQEngine:
    def __init__(self, processed_data, insights, rfm_df):
        self.df       = processed_data["df"]
        self.insights = insights
        self.rfm_df   = rfm_df
        self.monthly  = processed_data["monthly_sales"]
        self.products = processed_data["product_sales"]
        self.customers= processed_data["customer_sales"]
        self.countries= processed_data["country_sales"]

    def query(self, question):
        log(f"NLQ: {question}")
        q = question.lower().strip()

        # ── Revenue queries ──────────────────────────────
        if any(w in q for w in ["revenue", "sales", "income", "earn"]):
            month = self._extract_month(q)
            country = self._extract_country(q)
            product = self._extract_product(q)

            if month and not country and not product:
                return self._revenue_for_month(month)
            if country:
                return self._revenue_for_country(country)
            if product:
                return self._revenue_for_product(product)
            if "total" in q or "overall" in q or "all" in q:
                return f"💷 Total revenue across all time is **£{self.insights['total_revenue']:,.2f}**."
            if "best" in q or "highest" in q or "top" in q:
                best = list(self.monthly["Revenue"].items()) if hasattr(self.monthly["Revenue"], "items") else []
                if len(self.monthly) > 0:
                    rev_series = self.monthly["Revenue"]
                    best_month = str(rev_series.idxmax())
                    best_val   = rev_series.max()
                    return f"📈 Best month was **{best_month}** with revenue of **£{best_val:,.2f}**."
            if "lowest" in q or "worst" in q:
                rev_series  = self.monthly["Revenue"]
                worst_month = str(rev_series.idxmin())
                worst_val   = rev_series.min()
                return f"📉 Lowest month was **{worst_month}** with revenue of **£{worst_val:,.2f}**."
            month = self._extract_month(q)
            if month:
                return self._revenue_for_month(month)
            return f"💷 Total all-time revenue is **£{self.insights['total_revenue']:,.2f}** across **{self.insights['total_orders']:,}** orders."

        # ── Order queries ────────────────────────────────
        if any(w in q for w in ["order", "invoice", "transaction", "purchase"]):
            month = self._extract_month(q)
            if month:
                return self._orders_for_month(month)
            return f"🛒 Total orders placed: **{self.insights['total_orders']:,}**."

        # ── Customer queries ─────────────────────────────
        if any(w in q for w in ["customer", "buyer", "client"]):
            if "how many" in q or "count" in q or "total" in q:
                return f"👤 The system has **{self.insights['total_customers']:,}** unique customers."
            if "top" in q or "best" in q or "highest" in q:
                top = self.insights["top_customers"]
                if top:
                    c = top[0]
                    return f"👑 Top customer is **{c['CustomerID']}** with **£{c['Revenue']:,.2f}** in total purchases."
            if "champion" in q or "loyal" in q or "vip" in q:
                champs = self.rfm_df[self.rfm_df["Segment"] == "Champions"] if "Segment" in self.rfm_df.columns else []
                n = len(champs)
                return f"👑 There are **{n}** Champion customers (highest RFM score)."
            if "risk" in q or "churn" in q or "lost" in q:
                at_risk = self.rfm_df[self.rfm_df["Segment"].isin(["At Risk","Lost"])] if "Segment" in self.rfm_df.columns else []
                return f"⚠️ **{len(at_risk)}** customers are At Risk or Lost and need re-engagement."
            return f"👤 Total unique customers: **{self.insights['total_customers']:,}**. Average order value: **£{self.insights['avg_order_value']:,.2f}**."

        # ── Product queries ──────────────────────────────
        if any(w in q for w in ["product", "item", "stock", "sell", "selling"]):
            if "top" in q or "best" in q or "most" in q:
                top = self.insights["top_products"]
                if top:
                    p = top[0]
                    return f"📦 Best-selling product is **{p['Description']}** with **£{p['Revenue']:,.2f}** in revenue."
            if "how many" in q or "count" in q or "total" in q:
                return f"📦 There are **{self.insights['total_products']:,}** unique products in the dataset."
            product = self._extract_product(q)
            if product:
                return self._revenue_for_product(product)
            return f"📦 **{self.insights['total_products']:,}** unique products. Top seller: **{self.insights['top_products'][0]['Description'] if self.insights['top_products'] else 'N/A'}**."

        # ── Country queries ──────────────────────────────
        if any(w in q for w in ["country", "region", "location", "where", "uk", "germany", "france"]):
            country = self._extract_country(q)
            if country:
                return self._revenue_for_country(country)
            top = self.insights["top_countries"]
            if top:
                c = top[0]
                return f"🌍 Top country is **{c['Country']}** with **£{c['Revenue']:,.2f}** in revenue from **{c['Customers']}** customers."

        # ── Growth / trend queries ───────────────────────
        if any(w in q for w in ["growth", "trend", "growing", "declining", "increase", "decrease"]):
            gr = self.insights["growth_rate"]
            tl = self.insights["trend_label"]
            direction = "growing" if gr > 0 else "declining"
            return f"📊 Revenue trend is **{tl}** — {direction} at **{abs(gr):.1f}%** month-on-month average."

        # ── Average order value ──────────────────────────
        if any(w in q for w in ["average", "avg", "aov", "mean"]):
            return f"💡 Average order value is **£{self.insights['avg_order_value']:,.2f}**."

        # ── Greeting / help ──────────────────────────────
        if any(w in q for w in ["hello", "hi", "hey", "help", "what can"]):
            return ("👋 I can answer questions like: *What was the revenue in November?*, "
                    "*Who is the top customer?*, *What is the best-selling product?*, "
                    "*How many orders were placed?*, *What is the sales trend?*, "
                    "*Which country has the highest revenue?*")

        return ("🤔 I didn't quite understand that. Try asking about **revenue**, **orders**, "
                "**customers**, **products**, **countries**, or **trends**. "
                "Type *help* for examples.")

    # ── Helpers ─────────────────────────────────────────
    def _extract_month(self, q):
        for name, num in MONTHS.items():
            if name in q:
                return num
        m = re.search(r'\b(1[0-2]|[1-9])\b', q)
        return int(m.group()) if m else None

    def _extract_country(self, q):
        for country in self.countries.index if hasattr(self.countries, "index") else []:
            if country.lower() in q:
                return country
        for keyword, country in [("uk","United Kingdom"),("united kingdom","United Kingdom"),
                                   ("germany","Germany"),("france","France"),
                                   ("australia","Australia"),("netherlands","Netherlands")]:
            if keyword in q:
                return country
        return None

    def _extract_product(self, q):
        products = self.products.index if hasattr(self.products, "index") else []
        for prod in products:
            if prod.lower()[:12] in q:
                return prod
        return None

    def _revenue_for_month(self, month_num):
        try:
            rev_series = self.monthly["Revenue"]
            matches = {k: v for k, v in rev_series.items()
                       if str(k).endswith(f"-{month_num:02d}") or str(k).endswith(f"-{month_num}")}
            if matches:
                total = sum(matches.values())
                month_name = [k for k,v in MONTHS.items() if v == month_num and len(k) > 3][0].capitalize()
                return f"💷 Revenue for **{month_name}**: **£{total:,.2f}** across {len(matches)} year(s)."
            return f"🤔 No data found for month {month_num}."
        except Exception:
            return "🤔 Could not retrieve monthly revenue. Try asking for a specific month name."

    def _orders_for_month(self, month_num):
        try:
            ord_series = self.monthly["Orders"]
            matches = {k: v for k, v in ord_series.items()
                       if str(k).endswith(f"-{month_num:02d}") or str(k).endswith(f"-{month_num}")}
            if matches:
                total = sum(matches.values())
                month_name = [k for k,v in MONTHS.items() if v == month_num and len(k) > 3][0].capitalize()
                return f"🛒 Orders in **{month_name}**: **{total:,}** total."
            return f"🤔 No order data for month {month_num}."
        except Exception:
            return "🤔 Could not retrieve order count."

    def _revenue_for_country(self, country):
        try:
            row = self.countries.loc[country] if country in self.countries.index else None
            if row is not None:
                return f"🌍 **{country}** generated **£{row['Revenue']:,.2f}** revenue from **{int(row['Customers'])}** customers and **{int(row['Orders'])}** orders."
            return f"🤔 No data found for **{country}**."
        except Exception:
            return f"🤔 Could not retrieve data for {country}."

    def _revenue_for_product(self, product):
        try:
            row = self.products.loc[product] if product in self.products.index else None
            if row is not None:
                return f"📦 **{product}** generated **£{row['Revenue']:,.2f}** revenue with **{int(row['UnitsSold'])}** units sold."
            return f"🤔 No product found matching that description."
        except Exception:
            return "🤔 Could not retrieve product data."