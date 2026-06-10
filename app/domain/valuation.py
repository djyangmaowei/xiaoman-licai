from dataclasses import dataclass
from decimal import Decimal

from app.domain.ledger import quantize_money, quantize_nav


@dataclass(frozen=True)
class HoldingValue:
    code: str
    market_value: Decimal


@dataclass(frozen=True)
class DailyValuation:
    total_assets: Decimal
    unit_nav: Decimal


def calculate_daily_valuation(
    cash: Decimal,
    total_shares: Decimal,
    holdings: list[HoldingValue],
) -> DailyValuation:
    total_holdings = sum((holding.market_value for holding in holdings), Decimal("0"))
    total_assets = quantize_money(cash + total_holdings)
    unit_nav = Decimal("1.0000") if total_shares == 0 else quantize_nav(total_assets / total_shares)
    return DailyValuation(total_assets=total_assets, unit_nav=unit_nav)
