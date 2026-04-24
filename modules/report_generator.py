import os
import pandas as pd
from config import REPORTS_DIR
from utils.logger import log

class ReportGenerator:
    def generate(self, insights, rfm_df, recommendations):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        log("Generating reports...")

        # Convert list-of-dicts to DataFrames for export
        pd.DataFrame(insights["top_products"]).to_csv(
            f"{REPORTS_DIR}/top_products.csv", index=False)

        pd.DataFrame(insights["top_customers"]).to_csv(
            f"{REPORTS_DIR}/customers.csv", index=False)

        pd.DataFrame(insights["top_countries"]).to_csv(
            f"{REPORTS_DIR}/countries.csv", index=False)

        rfm_df.to_csv(f"{REPORTS_DIR}/rfm_segments.csv", index=False)

        # Excel workbook
        excel_path = f"{REPORTS_DIR}/full_report.xlsx"
        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                pd.DataFrame(insights["top_products"]).to_excel(
                    writer, sheet_name='Top Products', index=False)
                pd.DataFrame(insights["top_customers"]).to_excel(
                    writer, sheet_name='Top Customers', index=False)
                pd.DataFrame(insights["top_countries"]).to_excel(
                    writer, sheet_name='Country Sales', index=False)
                rfm_df.to_excel(
                    writer, sheet_name='RFM Analysis', index=False)
        except Exception as e:
            log(f"Excel export skipped: {e}", "warning")
            excel_path = None

        log("Reports generated successfully")
        return {
            "csv_path":      f"{REPORTS_DIR}/top_products.csv",
            "customer_path": f"{REPORTS_DIR}/customers.csv",
            "rfm_path":      f"{REPORTS_DIR}/rfm_segments.csv",
            "excel_path":    excel_path,
        }