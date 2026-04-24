import pandas as pd
from utils.logger import log

REQUIRED_COLUMNS = [
    'InvoiceNo', 'StockCode', 'Description', 'Quantity',
    'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country'
]

class DataImporter:
    def __init__(self, path):
        self.path = path

    def load(self):
        log(f"Loading dataset from {self.path}...")
        try:
            df = pd.read_csv(self.path, encoding='ISO-8859-1')
            log(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
            return df
        except FileNotFoundError:
            log(f"Dataset not found at {self.path}. Generating sample data.", "warning")
            return self._generate_sample_data()

    def validate(self, df):
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                raise Exception(f"Missing required column: {col}")
        log("Dataset validation successful")

    def _generate_sample_data(self):
        import numpy as np
        import random
        from datetime import datetime, timedelta

        np.random.seed(42)
        n = 2000
        products = [
            "WHITE HANGING HEART T-LIGHT HOLDER", "REGENCY CAKESTAND 3 TIER",
            "JUMBO BAG RED RETROSPOT", "PARTY BUNTING", "LUNCH BAG RED RETROSPOT",
            "ASSORTED COLOUR BIRD ORNAMENT", "POPCORN HOLDER", "SET OF 3 CAKE TINS",
            "ALARM CLOCK BAKELIKE GREEN", "STRAWBERRY CERAMIC TRINKET BOX",
            "WOODEN PICTURE FRAME WHITE FINISH", "CREAM CUPID HEARTS COAT HANGER",
            "HAND WARMER RED POLKA DOT", "VINTAGE UNION JACK MEMOBOARD",
        ]
        countries = ["United Kingdom", "Germany", "France", "Netherlands",
                     "Australia", "Spain", "Switzerland", "Belgium"]
        customer_ids = [round(x) for x in np.random.uniform(12000, 18500, 300)]
        start_date = datetime(2010, 12, 1)

        data = {
            'InvoiceNo': [f"5{i:05d}" for i in range(n)],
            'StockCode': [f"{random.randint(20000, 90000)}" for _ in range(n)],
            'Description': np.random.choice(products, n),
            'Quantity': np.random.randint(1, 50, n),
            'InvoiceDate': [(start_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d %H:%M:%S') for _ in range(n)],
            'UnitPrice': np.round(np.random.uniform(0.5, 25.0, n), 2),
            'CustomerID': np.random.choice(customer_ids, n),
            'Country': np.random.choice(countries, n, p=[0.7, 0.05, 0.07, 0.04, 0.04, 0.04, 0.03, 0.03])
        }
        log("Sample dataset generated with 2000 rows")
        return pd.DataFrame(data)