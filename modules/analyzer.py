from utils.logger import log
from utils.helpers import get_trend_label


class Analyzer:
    def analyze(self, processed, date_from=None, date_to=None):
        log("Analyzing data...")

        df = processed["df"].copy()

        if date_from:
            df = df[df["InvoiceDate"] >= date_from]
        if date_to:
            df = df[df["InvoiceDate"] <= date_to]

        if df.empty:
            log("No data in selected date range", "warning")
            return self._empty_insights()

        import pandas as pd

        product_sales = (
            df.groupby("Description")
            .agg(Revenue=("Revenue","sum"), UnitsSold=("Quantity","sum"), Orders=("InvoiceNo","nunique"))
            .sort_values("Revenue", ascending=False)
        )
        customer_sales = (
            df.groupby("CustomerID")
            .agg(Revenue=("Revenue","sum"), Orders=("InvoiceNo","nunique"), Items=("Quantity","sum"))
            .sort_values("Revenue", ascending=False)
        )
        monthly_sales = (
            df.groupby(df["InvoiceDate"].dt.to_period("M"))
            .agg(Revenue=("Revenue","sum"), Orders=("InvoiceNo","nunique"))
        )
        monthly_sales.index = monthly_sales.index.astype(str)

        country_sales = (
            df.groupby("Country")
            .agg(Revenue=("Revenue","sum"), Customers=("CustomerID","nunique"), Orders=("InvoiceNo","nunique"))
            .sort_values("Revenue", ascending=False)
        )

        total_revenue   = round(float(df["Revenue"].sum()), 2)
        total_orders    = int(df["InvoiceNo"].nunique())
        total_customers = int(df["CustomerID"].nunique())
        total_products  = int(df["Description"].nunique())
        avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0

        growth_rate = monthly_sales["Revenue"].pct_change().mean()
        growth_rate = round(float(growth_rate) * 100, 2) if growth_rate == growth_rate else 0
        trend_label = get_trend_label(growth_rate / 100)

        # ── Seasonal heatmap ── ensure plain Python floats
        dow_order   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        month_order = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]

        df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
        df["Month"]     = df["InvoiceDate"].dt.month_name()

        dow_rev   = df.groupby("DayOfWeek")["Revenue"].sum().reindex(dow_order, fill_value=0)
        month_rev = df.groupby("Month")["Revenue"].sum().reindex(month_order, fill_value=0)

        heatmap_dow   = {k: round(float(v), 2) for k, v in dow_rev.items()}
        heatmap_month = {k: round(float(v), 2) for k, v in month_rev.items()}

        # ── Convert to plain Python types for JSON safety ──
        monthly_labels   = list(monthly_sales.index)
        monthly_revenues = [round(float(v), 2) for v in monthly_sales["Revenue"].tolist()]
        monthly_orders   = [int(v) for v in monthly_sales["Orders"].tolist()]

        top_products = product_sales.head(10).reset_index().to_dict(orient="records")
        top_products = [{k: (round(float(v), 2) if isinstance(v, float) else
                             (int(v) if hasattr(v, '__int__') and not isinstance(v, str) else v))
                         for k, v in row.items()} for row in top_products]

        top_customers = customer_sales.head(10).reset_index().to_dict(orient="records")
        top_customers = [{k: (round(float(v), 2) if isinstance(v, float) else
                              (int(v) if hasattr(v, '__int__') and not isinstance(v, str) else v))
                          for k, v in row.items()} for row in top_customers]

        top_countries = country_sales.head(8).reset_index().to_dict(orient="records")
        top_countries = [{k: (round(float(v), 2) if isinstance(v, float) else
                              (int(v) if hasattr(v, '__int__') and not isinstance(v, str) else v))
                          for k, v in row.items()} for row in top_countries]

        log("Analysis complete")
        return {
            "total_revenue":    total_revenue,
            "total_orders":     total_orders,
            "total_customers":  total_customers,
            "total_products":   total_products,
            "avg_order_value":  avg_order_value,
            "growth_rate":      growth_rate,
            "trend_label":      trend_label,
            "monthly_labels":   monthly_labels,
            "monthly_revenues": monthly_revenues,
            "monthly_orders":   monthly_orders,
            "top_products":     top_products,
            "bottom_products":  product_sales.tail(5).reset_index().to_dict(orient="records"),
            "top_customers":    top_customers,
            "top_countries":    top_countries,
            "heatmap_dow":      heatmap_dow,
            "heatmap_month":    heatmap_month,
        }

    def _empty_insights(self):
        return {
            "total_revenue": 0, "total_orders": 0, "total_customers": 0,
            "total_products": 0, "avg_order_value": 0, "growth_rate": 0,
            "trend_label": "No Data", "monthly_labels": [], "monthly_revenues": [],
            "monthly_orders": [], "top_products": [], "bottom_products": [],
            "top_customers": [], "top_countries": [],
            "heatmap_dow": {}, "heatmap_month": {},
        }