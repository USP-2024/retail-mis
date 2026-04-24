import pandas as pd
from utils.logger import log

class RFMAnalyzer:
    def compute(self, df):
        log("Computing RFM analysis...")

        snapshot = df['InvoiceDate'].max() + pd.Timedelta(days=1)

        rfm = df.groupby('CustomerID').agg(
            Recency=('InvoiceDate', lambda x: (snapshot - x.max()).days),
            Frequency=('InvoiceNo', 'nunique'),
            Monetary=('Revenue', 'sum')
        ).round(2)

        # Score each dimension 1-4
        rfm['R_Score'] = pd.qcut(rfm['Recency'], q=4, labels=[4, 3, 2, 1], duplicates='drop')
        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=4, labels=[1, 2, 3, 4], duplicates='drop')
        rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=4, labels=[1, 2, 3, 4], duplicates='drop')

        rfm['RFM_Score'] = (
            rfm['R_Score'].astype(int) +
            rfm['F_Score'].astype(int) +
            rfm['M_Score'].astype(int)
        )

        rfm['Segment'] = rfm['RFM_Score'].apply(self._segment_label)

        log("RFM analysis complete")
        return rfm.reset_index()

    def _segment_label(self, score):
        if score >= 10:
            return "Champions"
        elif score >= 8:
            return "Loyal Customers"
        elif score >= 6:
            return "Potential Loyalists"
        elif score >= 4:
            return "At Risk"
        else:
            return "Lost"

    def segment_summary(self, rfm_df):
        return (
            rfm_df.groupby('Segment')
            .agg(Count=('CustomerID', 'count'), AvgMonetary=('Monetary', 'mean'))
            .round(2)
            .reset_index()
            .sort_values('Count', ascending=False)
        )