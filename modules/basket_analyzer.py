import pandas as pd
from itertools import combinations
from utils.logger import log


class BasketAnalyzer:
    def analyze(self, df, min_support=0.02, top_n=10):
        log("Running market basket analysis...")
        # Always use co-occurrence — mlxtend runs out of memory on large datasets
        return self._cooccurrence_method(df, top_n)

    def _cooccurrence_method(self, df, top_n):
        """Pure pandas co-occurrence — memory-safe for large datasets."""
        # Limit to top 100 products by frequency to keep it fast
        top_products = (
            df.groupby("Description")["InvoiceNo"]
            .nunique()
            .sort_values(ascending=False)
            .head(100)
            .index.tolist()
        )
        df_filtered = df[df["Description"].isin(top_products)]

        invoice_products = (
            df_filtered.groupby("InvoiceNo")["Description"]
            .apply(lambda x: list(set(x)))
        )

        pair_counts    = {}
        total_invoices = df["InvoiceNo"].nunique()

        for products in invoice_products:
            if len(products) < 2:
                continue
            for a, b in combinations(sorted(products), 2):
                pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

        if not pair_counts:
            log("No product pairs found")
            return []

        sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
        item_freq    = df.groupby("Description")["InvoiceNo"].nunique().to_dict()

        results = []
        for (a, b), count in sorted_pairs[:top_n]:
            support    = round(count / total_invoices * 100, 2)
            confidence = round(count / max(item_freq.get(a, 1), 1) * 100, 2)
            freq_a     = item_freq.get(a, 1) / total_invoices
            freq_b     = item_freq.get(b, 1) / total_invoices
            lift       = round((count / total_invoices) / max(freq_a * freq_b, 1e-9), 2)
            results.append({
                "antecedent": a,
                "consequent":  b,
                "support":     support,
                "confidence":  confidence,
                "lift":        lift,
            })

        log(f"Basket analysis complete: {len(results)} pairs found")
        return results