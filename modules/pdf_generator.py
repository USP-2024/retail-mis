import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from datetime import datetime
from config import REPORTS_DIR, CHARTS_DIR
from utils.logger import log


class PDFGenerator:
    def generate(self, insights, rfm_summary, recommendations):
        log("Generating PDF report...")
        try:
            from fpdf import FPDF
            return self._fpdf_report(insights, rfm_summary, recommendations)
        except ImportError:
            log("fpdf2 not installed, generating matplotlib PDF", "warning")
            return self._matplotlib_pdf(insights, rfm_summary, recommendations)

    # ── fpdf2 version ────────────────────────────────────────────────────────
    def _fpdf_report(self, insights, rfm_summary, recommendations):
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # ── Cover header ──
        pdf.set_fill_color(6, 13, 31)
        pdf.rect(0, 0, 210, 45, 'F')
        pdf.set_text_color(168, 240, 222)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_xy(10, 8)
        pdf.cell(0, 10, "RetailMIS - Executive Report", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(150, 170, 200)
        pdf.set_xy(10, 22)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", ln=True)
        pdf.set_xy(10, 30)
        pdf.cell(0, 8, "Online Retail Sales & Customer Decision Support MIS", ln=True)

        pdf.set_y(52)
        pdf.set_text_color(30, 30, 30)

        # ── KPI Summary ──
        self._fpdf_section(pdf, "Key Performance Indicators")
        kpis = [
            ("Total Revenue",     f"GBP {insights['total_revenue']:,.2f}"),
            ("Total Orders",      f"{insights['total_orders']:,}"),
            ("Unique Customers",  f"{insights['total_customers']:,}"),
            ("Unique Products",   f"{insights['total_products']:,}"),
            ("Avg Order Value",   f"GBP {insights['avg_order_value']:,.2f}"),
            ("Growth Rate",       f"{insights['growth_rate']}% ({insights['trend_label']})"),
        ]
        pdf.set_font("Helvetica", "", 10)
        for label, value in kpis:
            pdf.set_fill_color(240, 245, 255)
            pdf.cell(90, 8, f"  {label}", border=0, fill=True)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(90, 8, value, border=0, ln=True)
            pdf.set_font("Helvetica", "", 10)
        pdf.ln(4)

        # ── Top Products ──
        self._fpdf_section(pdf, "Top 10 Products by Revenue")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(15, 28, 53)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 7, "Product", fill=True)
        pdf.cell(40,  7, "Revenue (GBP)", fill=True)
        pdf.cell(30,  7, "Units Sold", fill=True, ln=True)
        pdf.set_text_color(30, 30, 30)
        for i, p in enumerate(insights["top_products"][:10]):
            pdf.set_fill_color(245, 248, 255) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "", 9)
            desc = str(p["Description"])[:48]
            pdf.cell(100, 6, f"  {desc}", fill=True)
            pdf.cell(40,  6, f"{p['Revenue']:,.2f}", fill=True)
            pdf.cell(30,  6, f"{int(p['UnitsSold']):,}", fill=True, ln=True)
        pdf.ln(4)

        # ── RFM Segments ──
        self._fpdf_section(pdf, "RFM Customer Segmentation")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(15, 28, 53)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(70, 7, "Segment", fill=True)
        pdf.cell(40, 7, "Customers", fill=True)
        pdf.cell(60, 7, "Avg Monetary Value (GBP)", fill=True, ln=True)
        pdf.set_text_color(30, 30, 30)
        for i, seg in enumerate(rfm_summary):
            pdf.set_fill_color(245, 248, 255) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(70, 6, f"  {seg['Segment']}", fill=True)
            pdf.cell(40, 6, str(seg['Count']), fill=True)
            pdf.cell(60, 6, f"{seg['AvgMonetary']:,.2f}", fill=True, ln=True)
        pdf.ln(4)

        # ── Recommendations ──
        self._fpdf_section(pdf, "AI-Powered Recommendations")
        pdf.set_font("Helvetica", "", 10)
        for rec in recommendations:
            pdf.set_font("Helvetica", "B", 10)
            title = f"{rec['icon']} {rec['title']}"
            pdf.cell(0, 7, title.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            detail = rec['detail'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, f"   {detail}")
            pdf.set_text_color(30, 30, 30)
            pdf.ln(2)

        # ── Charts page ──
        pdf.add_page()
        self._fpdf_section(pdf, "Visual Analytics")
        chart_files = ["trend.png", "products.png", "countries.png"]
        y_pos = pdf.get_y()
        for i, fname in enumerate(chart_files):
            path = os.path.join(CHARTS_DIR, fname)
            if os.path.exists(path):
                pdf.image(path, x=10, y=y_pos, w=185)
                y_pos += 75
                pdf.set_y(y_pos)

        path = os.path.join(REPORTS_DIR, "report.pdf")
        pdf.output(path)
        log(f"PDF saved to {path}")
        return path

    # ── Matplotlib fallback ──────────────────────────────────────────────────
    def _matplotlib_pdf(self, insights, rfm_summary, recommendations):
        from matplotlib.backends.backend_pdf import PdfPages

        path = os.path.join(REPORTS_DIR, "report.pdf")
        BG   = "#060d1f"
        CARD = "#0f1c35"
        MINT = "#a8f0de"
        LAV  = "#c9b8ff"
        TEXT = "#edf0f7"
        MUTED= "#5a6380"

        with PdfPages(path) as pdf:

            # ── Page 1: Cover + KPIs ──────────────────────────
            fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
            fig.text(0.5, 0.92, "RetailMIS — Executive Report",
                     ha='center', fontsize=26, fontweight='bold', color=MINT)
            fig.text(0.5, 0.87, "Online Retail Sales & Customer Decision Support MIS",
                     ha='center', fontsize=12, color=MUTED)
            fig.text(0.5, 0.84, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
                     ha='center', fontsize=10, color=MUTED)

            # KPI boxes
            kpis = [
                ("Total Revenue",    f"£{insights['total_revenue']:,.2f}",      MINT),
                ("Total Orders",     f"{insights['total_orders']:,}",            "#a8d8f0"),
                ("Unique Customers", f"{insights['total_customers']:,}",         LAV),
                ("Unique Products",  f"{insights['total_products']:,}",          "#ffc9a8"),
                ("Avg Order Value",  f"£{insights['avg_order_value']:,.2f}",     "#ffb8c8"),
                ("Growth Trend",     insights['trend_label'],                    "#b8f0c0"),
            ]
            for i, (label, value, color) in enumerate(kpis):
                col = i % 3
                row = i // 3
                x = 0.05 + col * 0.32
                y = 0.56 - row * 0.22
                ax = fig.add_axes([x, y, 0.28, 0.18])
                ax.set_facecolor(CARD)
                ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                ax.axis('off')
                ax.axhline(y=1, color=color, linewidth=3, xmin=0, xmax=1)
                ax.text(0.5, 0.65, value, ha='center', va='center',
                        fontsize=16, fontweight='bold', color=color,
                        fontfamily='monospace')
                ax.text(0.5, 0.25, label, ha='center', va='center',
                        fontsize=9, color=MUTED, fontweight='bold',
                        transform=ax.transAxes)

            # Top 5 products mini-table
            ax2 = fig.add_axes([0.05, 0.05, 0.9, 0.25])
            ax2.set_facecolor(CARD); ax2.axis('off')
            ax2.text(0.5, 0.92, "Top 5 Products by Revenue",
                     ha='center', fontsize=11, fontweight='bold',
                     color=TEXT, transform=ax2.transAxes)
            cols = ["#", "Product", "Revenue", "Units Sold"]
            col_x = [0.03, 0.08, 0.78, 0.91]
            for ci, (cx, ch) in enumerate(zip(col_x, cols)):
                ax2.text(cx, 0.78, ch, fontsize=8, color=MUTED,
                         fontweight='bold', transform=ax2.transAxes)
            for ri, p in enumerate(insights["top_products"][:5]):
                y_row = 0.62 - ri * 0.14
                row_color = MINT if ri == 0 else TEXT
                ax2.text(col_x[0], y_row, str(ri+1), fontsize=9,
                         color=MUTED, transform=ax2.transAxes, fontfamily='monospace')
                desc = str(p["Description"])[:50]
                ax2.text(col_x[1], y_row, desc, fontsize=8,
                         color=row_color, transform=ax2.transAxes)
                ax2.text(col_x[2], y_row, f"£{p['Revenue']:,.2f}", fontsize=9,
                         color=MINT, transform=ax2.transAxes, fontfamily='monospace')
                ax2.text(col_x[3], y_row, f"{int(p['UnitsSold']):,}", fontsize=9,
                         color=MUTED, transform=ax2.transAxes, fontfamily='monospace')
            pdf.savefig(fig, facecolor=BG); plt.close()

            # ── Page 2: Charts ────────────────────────────────
            fig2, axes = plt.subplots(2, 2, figsize=(11.69, 8.27), facecolor=BG)
            fig2.suptitle("Visual Analytics", fontsize=16, fontweight='bold',
                          color=MINT, y=0.98)
            palette = [MINT, LAV, "#ffc9a8", "#a8d8f0", "#ffb8c8",
                       "#b8f0c0", "#f0eda8", "#ffb8c8"]

            # Revenue trend
            ax = axes[0, 0]; ax.set_facecolor(CARD)
            labels = insights["monthly_labels"]; rev = insights["monthly_revenues"]
            ax.plot(range(len(labels)), rev, color=MINT, linewidth=2, marker='o', markersize=4)
            ax.fill_between(range(len(labels)), rev, alpha=0.15, color=MINT)
            step = max(1, len(labels)//6)
            ax.set_xticks(range(0, len(labels), step))
            ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)],
                               rotation=30, ha='right', fontsize=7, color=MUTED)
            ax.set_title("Monthly Revenue Trend", color=TEXT, fontsize=10, fontweight='bold')
            ax.yaxis.set_tick_params(labelcolor=MUTED, labelsize=7)
            for sp in ax.spines.values(): sp.set_color("#132240")
            ax.set_facecolor(CARD); fig2.patch.set_facecolor(BG)

            # Top products bar
            ax = axes[0, 1]; ax.set_facecolor(CARD)
            tp = insights["top_products"][:8]
            names = [p["Description"][:20] + "…" if len(p["Description"]) > 20
                     else p["Description"] for p in tp]
            revs  = [p["Revenue"] for p in tp]
            colors= [MINT] + [LAV] * (len(tp)-1)
            ax.barh(range(len(names)), revs[::-1], color=colors[::-1])
            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names[::-1], fontsize=7, color=MUTED)
            ax.set_title("Top Products by Revenue", color=TEXT, fontsize=10, fontweight='bold')
            ax.xaxis.set_tick_params(labelcolor=MUTED, labelsize=7)
            for sp in ax.spines.values(): sp.set_color("#132240")

            # Country donut
            ax = axes[1, 0]; ax.set_facecolor(CARD)
            tc = insights["top_countries"][:6]
            wedges, texts, autotexts = ax.pie(
                [c["Revenue"] for c in tc],
                labels=[c["Country"] for c in tc],
                autopct='%1.1f%%', colors=palette[:len(tc)],
                textprops={'color': MUTED, 'fontsize': 7},
                wedgeprops={'linewidth': 1.5, 'edgecolor': CARD}
            )
            for at in autotexts: at.set_color(TEXT); at.set_fontsize(7)
            ax.set_title("Revenue by Country", color=TEXT, fontsize=10, fontweight='bold')

            # RFM pie
            ax = axes[1, 1]; ax.set_facecolor(CARD)
            rfm_colors = ["#f0eda8", MINT, "#a8d8f0", "#ffc9a8", "#ffb8c8"]
            wedges, texts, autotexts = ax.pie(
                [s["Count"] for s in rfm_summary],
                labels=[s["Segment"] for s in rfm_summary],
                autopct='%1.1f%%', colors=rfm_colors[:len(rfm_summary)],
                textprops={'color': MUTED, 'fontsize': 7},
                wedgeprops={'linewidth': 1.5, 'edgecolor': CARD}
            )
            for at in autotexts: at.set_color(TEXT); at.set_fontsize(7)
            ax.set_title("RFM Customer Segments", color=TEXT, fontsize=10, fontweight='bold')

            plt.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig2, facecolor=BG); plt.close()

            # ── Page 3: Recommendations ───────────────────────
            fig3 = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
            fig3.text(0.5, 0.95, "AI-Powered Recommendations",
                      ha='center', fontsize=18, fontweight='bold', color=MINT)
            for i, rec in enumerate(recommendations[:6]):
                y_start = 0.85 - i * 0.13
                ax_r = fig3.add_axes([0.05, y_start - 0.09, 0.9, 0.11])
                ax_r.set_facecolor(CARD); ax_r.axis('off')
                cat_color = {"Sales Alert": "#ffb8b8", "Growth Opportunity": MINT,
                             "Customer Retention": LAV, "Win-Back Campaign": "#ffc9a8",
                             "Inventory Planning": "#a8d8f0",
                             "Revenue Optimization": "#f0eda8"}.get(rec.get("category",""), MINT)
                ax_r.text(0.01, 0.82, rec.get("category","").upper(),
                          fontsize=7, color=cat_color, fontweight='bold',
                          transform=ax_r.transAxes)
                title_text = f"{rec.get('icon','')} {rec.get('title','')}".encode('ascii','replace').decode()
                ax_r.text(0.01, 0.55, title_text,
                          fontsize=10, color=TEXT, fontweight='bold',
                          transform=ax_r.transAxes)
                detail = rec.get("detail","")[:130]
                ax_r.text(0.01, 0.18, detail,
                          fontsize=8, color=MUTED, transform=ax_r.transAxes,
                          wrap=True)
            pdf.savefig(fig3, facecolor=BG); plt.close()

        log(f"PDF report saved: {path}")
        return path

    def _fpdf_section(self, pdf, title):
        pdf.set_fill_color(15, 28, 53)
        pdf.set_text_color(168, 240, 222)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"  {title}", fill=True, ln=True)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(2)