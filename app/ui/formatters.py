from decimal import Decimal


def money(value: Decimal) -> str:
    return f"¥{value:,.2f}"


def number4(value: Decimal) -> str:
    return f"{value:,.4f}"


def percent(value: Decimal) -> str:
    return f"{value * Decimal('100'):.2f}%"
