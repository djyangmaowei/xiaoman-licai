from decimal import Decimal

from app.domain.ledger import (
    apply_buy_trade,
    apply_subscription,
    calculate_unit_nav,
)


def test_first_subscription_uses_initial_nav_one():
    result = apply_subscription(
        cash=Decimal("0"),
        total_shares=Decimal("0"),
        unit_nav=Decimal("1.0000"),
        amount=Decimal("10000"),
    )

    assert result.cash == Decimal("10000.00")
    assert result.total_shares == Decimal("10000.0000")


def test_later_subscription_uses_current_nav():
    result = apply_subscription(
        cash=Decimal("2000"),
        total_shares=Decimal("10000"),
        unit_nav=Decimal("1.2500"),
        amount=Decimal("2500"),
    )

    assert result.cash == Decimal("4500.00")
    assert result.total_shares == Decimal("12000.0000")


def test_buy_trade_reduces_cash_without_changing_total_shares():
    result = apply_buy_trade(
        cash=Decimal("10000"),
        total_shares=Decimal("10000"),
        gross_amount=Decimal("6000"),
        fee=Decimal("3"),
    )

    assert result.cash == Decimal("3997.00")
    assert result.total_shares == Decimal("10000")


def test_unit_nav_is_total_assets_divided_by_total_shares():
    nav = calculate_unit_nav(total_assets=Decimal("12345.67"), total_shares=Decimal("10000"))

    assert nav == Decimal("1.2346")
