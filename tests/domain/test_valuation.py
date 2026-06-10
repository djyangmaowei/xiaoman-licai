from decimal import Decimal

from app.domain.valuation import HoldingValue, calculate_daily_valuation


def test_daily_valuation_sums_cash_and_holdings():
    valuation = calculate_daily_valuation(
        cash=Decimal("4000"),
        total_shares=Decimal("10000"),
        holdings=[
            HoldingValue(code="515450", market_value=Decimal("3000")),
            HoldingValue(code="518880", market_value=Decimal("5000")),
        ],
    )

    assert valuation.total_assets == Decimal("12000.00")
    assert valuation.unit_nav == Decimal("1.2000")
