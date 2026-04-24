from utils.logger import log

class DataProcessor:
    def process(self, df):
        log("Processing data...")

        df = df.copy()
        df['Revenue'] = df['Quantity'] * df['UnitPrice']

        product_sales = (
            df.groupby('Description')
            .agg(Revenue=('Revenue', 'sum'), UnitsSold=('Quantity', 'sum'), Orders=('InvoiceNo', 'nunique'))
            .sort_values('Revenue', ascending=False)
        )

        customer_sales = (
            df.groupby('CustomerID')
            .agg(Revenue=('Revenue', 'sum'), Orders=('InvoiceNo', 'nunique'), Items=('Quantity', 'sum'))
            .sort_values('Revenue', ascending=False)
        )

        monthly_sales = (
            df.groupby(df['InvoiceDate'].dt.to_period('M'))
            .agg(Revenue=('Revenue', 'sum'), Orders=('InvoiceNo', 'nunique'))
        )
        monthly_sales.index = monthly_sales.index.astype(str)

        country_sales = (
            df.groupby('Country')
            .agg(Revenue=('Revenue', 'sum'), Customers=('CustomerID', 'nunique'), Orders=('InvoiceNo', 'nunique'))
            .sort_values('Revenue', ascending=False)
        )

        log("Processing complete")
        return {
            "df": df,
            "product_sales": product_sales,
            "customer_sales": customer_sales,
            "monthly_sales": monthly_sales,
            "country_sales": country_sales,
        }