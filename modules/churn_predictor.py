import numpy as np
from utils.logger import log


class ChurnPredictor:
    """
    Predicts churn risk from RFM scores using a simple
    rule-based + logistic approach (no external ML lib needed at runtime,
    but uses sklearn if available).
    """

    def predict(self, rfm_df):
        log("Running churn prediction...")
        try:
            df = rfm_df.copy()

            # Normalise columns
            for col in ["Recency", "Frequency", "Monetary"]:
                mn, mx = df[col].min(), df[col].max()
                rng = mx - mn if mx != mn else 1
                df[f"{col}_norm"] = (df[col] - mn) / rng

            # Churn score: high recency + low frequency + low monetary = high churn risk
            df["churn_score"] = (
                df["Recency_norm"] * 0.5 +
                (1 - df["Frequency_norm"]) * 0.3 +
                (1 - df["Monetary_norm"]) * 0.2
            )

            # Try sklearn for a real model
            try:
                from sklearn.linear_model import LogisticRegression
                from sklearn.preprocessing import StandardScaler

                X = df[["Recency_norm", "Frequency_norm", "Monetary_norm"]].values
                # Label: churn if score > 0.55
                y = (df["churn_score"] > 0.55).astype(int).values

                if y.sum() > 0 and (1 - y).sum() > 0:
                    scaler = StandardScaler()
                    X_sc   = scaler.fit_transform(X)
                    model  = LogisticRegression(max_iter=200)
                    model.fit(X_sc, y)
                    proba  = model.predict_proba(X_sc)[:, 1]
                    df["churn_prob"] = np.round(proba * 100, 1)
                else:
                    df["churn_prob"] = np.round(df["churn_score"] * 100, 1)

            except ImportError:
                df["churn_prob"] = np.round(df["churn_score"] * 100, 1)

            # Risk label
            df["churn_risk"] = df["churn_prob"].apply(self._risk_label)

            log("Churn prediction complete")
            return df[["CustomerID", "Recency", "Frequency", "Monetary",
                        "Segment", "churn_prob", "churn_risk"]]

        except Exception as e:
            log(f"Churn prediction error: {e}", "error")
            return rfm_df.assign(churn_prob=0, churn_risk="Unknown")

    @staticmethod
    def _risk_label(prob):
        if prob >= 70:
            return "High"
        elif prob >= 40:
            return "Medium"
        else:
            return "Low"