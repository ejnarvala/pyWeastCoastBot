def format_percent(value):
    return f"{value:.2f}%"


def format_money(value):
    result = f"${abs(value):,.2f}"
    if value < 0:
        result = f"-{result}"
    return result
