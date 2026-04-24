import pandas as pd
from utils.logger import log

class DataCleaner:
    def clean(self, df):
        original_len = len(df)
        log("Starting data cleaning...")

        # Drop rows with missing critical fields
        df = df.dropna(subset=['CustomerID', 'Description', 'InvoiceDate'])

        # Remove cancelled orders (InvoiceNo starting with 'C')
        df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]

        # Remove invalid quantities and prices
        df = df[df['Quantity'] > 0]
        df = df[df['UnitPrice'] > 0]

        # Parse dates
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
        df = df.dropna(subset=['InvoiceDate'])

        # Clean string fields
        df['Description'] = df['Description'].str.strip().str.title()
        df['Country'] = df['Country'].str.strip()

        # Cast types
        df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
        df['Quantity'] = df['Quantity'].astype(int)
        df['UnitPrice'] = df['UnitPrice'].astype(float)

        cleaned_len = len(df)
        log(f"Cleaning complete: {original_len - cleaned_len} rows removed, {cleaned_len} retained")
        return df