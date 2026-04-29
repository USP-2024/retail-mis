import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
from config import CHARTS_DIR
from utils.logger import log

DARK_BG = "#060d1f"
CARD_BG = "#0f1c35"
ACCENT  = "#a8f0de"
ACCENT2 = "#c9b8ff"
ACCENT3 = "#ffc9a8"
TEXT    = "#edf0f7"
MUTED   = "#5a6380"
GRID    = "#132240"

def _style_fig(fig, ax):
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(CARD_BG)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)

class Visualizer:
    def plot(self, insights):
        os.makedirs(CHARTS_DIR, exist_ok=True)
        self._plot_top_products(insights)
        self._plot_revenue_trend(insights)
        self._plot_countries(insights)
        log("Charts generated successfully")

    def _plot_top_products(self, insights):
        records = insights["top_products"][:10]
        if not records:
            return
        descriptions = [r['Description'] for r in records][::-1]
        revenues     = [r['Revenue']     for r in records][::-1]
        n      = len(records)
        colors = ([ACCENT] + [ACCENT2] * max(n - 1, 0))[::-1]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(range(n), revenues, color=colors)
        ax.set_yticks(range(n))
        ax.set_yticklabels(descriptions, fontsize=8)
        _style_fig(fig, ax)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
        ax.set_title("Top Products by Revenue", fontsize=13, fontweight='bold', pad=15)
        ax.grid(axis='x', color=GRID, linewidth=0.5)
        plt.tight_layout()
        plt.savefig(f"{CHARTS_DIR}/products.png", dpi=120, bbox_inches='tight', facecolor=DARK_BG)
        plt.close()

    def _plot_revenue_trend(self, insights):
        labels   = insights["monthly_labels"]
        revenues = insights["monthly_revenues"]
        if not labels:
            return
        x = list(range(len(labels)))
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(x, revenues, color=ACCENT, linewidth=2.5, marker='o', markersize=5)
        ax.fill_between(x, revenues, alpha=0.15, color=ACCENT)
        step = max(1, len(labels) // 8)
        tick_positions = list(range(0, len(labels), step))
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([labels[i] for i in tick_positions],
                           rotation=45, ha='right', fontsize=8)
        _style_fig(fig, ax)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
        ax.set_title("Monthly Revenue Trend", fontsize=13, fontweight='bold', pad=15)
        ax.grid(axis='y', color=GRID, linewidth=0.5)
        plt.tight_layout()
        plt.savefig(f"{CHARTS_DIR}/trend.png", dpi=120, bbox_inches='tight', facecolor=DARK_BG)
        plt.close()

    def _plot_countries(self, insights):
        records = insights["top_countries"][:8]
        if not records:
            return
        countries = [r['Country'] for r in records]
        revenues  = [r['Revenue'] for r in records]
        colors    = [ACCENT, ACCENT2, ACCENT3, "#a8d8f0", "#ffb8c8",
                     "#b8f0c0", "#f0eda8", "#c9b8ff"]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(range(len(countries)), revenues, color=colors[:len(records)])
        ax.set_xticks(range(len(countries)))
        ax.set_xticklabels(countries, rotation=30, ha='right', fontsize=8)
        _style_fig(fig, ax)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
        ax.set_title("Revenue by Country", fontsize=13, fontweight='bold', pad=15)
        ax.grid(axis='y', color=GRID, linewidth=0.5)
        plt.tight_layout()
        plt.savefig(f"{CHARTS_DIR}/countries.png", dpi=120, bbox_inches='tight', facecolor=DARK_BG)
        plt.close()