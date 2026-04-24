from utils.logger import log

class Recommender:
    def generate(self, insights, rfm_df):
        log("Generating recommendations...")
        recs = []

        # Growth-based recommendation
        growth = insights.get("growth_rate", 0)
        if growth < -5:
            recs.append({
                "icon": "📉",
                "category": "Sales Alert",
                "title": "Revenue Declining",
                "detail": f"Monthly sales trend is down {abs(growth):.1f}%. Consider launching discount campaigns or promotions to recover momentum."
            })
        elif growth > 10:
            recs.append({
                "icon": "🚀",
                "category": "Growth Opportunity",
                "title": "Strong Revenue Growth",
                "detail": f"Sales are up {growth:.1f}% monthly. Invest in scaling inventory for top-selling products to capitalize on momentum."
            })
        else:
            recs.append({
                "icon": "📊",
                "category": "Performance",
                "title": "Stable Revenue Trend",
                "detail": "Revenue is relatively stable. Consider seasonal campaigns and upselling to top customers to accelerate growth."
            })

        # VIP customers
        if not rfm_df.empty:
            champions = rfm_df[rfm_df['Segment'] == 'Champions']
            at_risk = rfm_df[rfm_df['Segment'] == 'At Risk']
            lost = rfm_df[rfm_df['Segment'] == 'Lost']

            if len(champions) > 0:
                recs.append({
                    "icon": "👑",
                    "category": "Customer Retention",
                    "title": f"{len(champions)} Champion Customers Identified",
                    "detail": "Reward these top customers with exclusive loyalty benefits or early-access promotions to maintain their engagement."
                })

            if len(at_risk) > 0:
                recs.append({
                    "icon": "⚠️",
                    "category": "Win-Back Campaign",
                    "title": f"{len(at_risk)} Customers At Risk",
                    "detail": "These customers haven't purchased recently but have good historical value. Send personalized re-engagement emails or special offers."
                })

            if len(lost) > 5:
                recs.append({
                    "icon": "🔄",
                    "category": "Re-Engagement",
                    "title": f"{len(lost)} Lost Customers",
                    "detail": "Consider a win-back campaign with aggressive discounts to recover lapsed customers before they switch to competitors."
                })

        # Product-based
        top_products = insights.get("top_products")
        if top_products and len(top_products) > 0:
            top_name = top_products[0].get('Description', 'Top Product')
            recs.append({
                "icon": "📦",
                "category": "Inventory Planning",
                "title": f"Stock Up on Best-Sellers",
                "detail": f'"{top_name}" is your highest revenue product. Ensure sufficient stock and consider bundling it with slower-moving items.'
            })

        # AOV recommendation
        aov = insights.get("avg_order_value", 0)
        if aov < 20:
            recs.append({
                "icon": "💡",
                "category": "Revenue Optimization",
                "title": "Increase Average Order Value",
                "detail": f"Current AOV is £{aov:.2f}. Introduce minimum order free-shipping thresholds or bundle deals to encourage larger purchases."
            })

        log(f"{len(recs)} recommendations generated")
        return recs