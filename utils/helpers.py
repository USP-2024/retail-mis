def format_currency(value):
    return f"£{value:,.2f}"

def format_number(value):
    return f"{value:,}"

def safe_divide(a, b):
    return a / b if b != 0 else 0

def get_trend_label(rate):
    if rate > 0.05:
        return "Strong Growth"
    elif rate > 0:
        return "Moderate Growth"
    elif rate == 0:
        return "Stable"
    elif rate > -0.05:
        return "Slight Decline"
    else:
        return "Declining"