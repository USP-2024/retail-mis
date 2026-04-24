import numpy as np
from utils.logger import log


class Forecaster:
    def forecast(self, monthly_sales_series, periods=3):
        log("Running revenue forecast...")
        try:
            labels  = list(monthly_sales_series.keys())
            values  = list(monthly_sales_series.values())
            n       = len(values)

            if n < 3:
                return {"forecast_labels": [], "forecast_values": [],
                        "upper": [], "lower": [], "r2": 0, "slope": 0}

            x = np.arange(n)
            y = np.array(values, dtype=float)

            coeffs           = np.polyfit(x, y, deg=1)
            slope, intercept = float(coeffs[0]), float(coeffs[1])
            y_pred           = np.polyval(coeffs, x)
            residuals        = y - y_pred
            std_err          = float(np.std(residuals))

            ss_res = float(np.sum(residuals ** 2))
            ss_tot = float(np.sum((y - np.mean(y)) ** 2))
            r2     = round(1 - ss_res / ss_tot, 3) if ss_tot != 0 else 0

            # Future month labels
            last_label = labels[-1]
            try:
                year, month = int(last_label[:4]), int(last_label[5:7])
            except Exception:
                year, month = 2011, 12

            future_labels = []
            for i in range(1, periods + 1):
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                future_labels.append(f"{year}-{month:02d}")

            future_x      = np.arange(n, n + periods)
            # ── Ensure plain Python floats for JSON serialisation ──
            future_values = [round(float(max(0, np.polyval(coeffs, xi))), 2) for xi in future_x]
            upper         = [round(float(v + 1.5 * std_err), 2) for v in future_values]
            lower         = [round(float(max(0, v - 1.5 * std_err)), 2) for v in future_values]

            log(f"Forecast complete: slope={slope:.2f}, R²={r2}")
            return {
                "forecast_labels": future_labels,
                "forecast_values": future_values,
                "upper":  upper,
                "lower":  lower,
                "r2":     float(r2),
                "slope":  round(float(slope), 2),
            }

        except Exception as e:
            log(f"Forecast error: {e}", "error")
            return {"forecast_labels": [], "forecast_values": [],
                    "upper": [], "lower": [], "r2": 0, "slope": 0}