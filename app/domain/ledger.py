from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANT = Decimal("0.01")
SHARE_QUANT = Decimal("0.0001")
NAV_QUANT = Decimal("0.0001")


@dataclass(frozen=True)
class LedgerState:
    cash: Decimal
    total_shares: Decimal


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def quantize_shares(value: Decimal) -> Decimal:
    return value.quantize(SHARE_QUANT, rounding=ROUND_HALF_UP)


def quantize_nav(value: Decimal) -> Decimal:
    return value.quantize(NAV_QUANT, rounding=ROUND_HALF_UP)


def apply_subscription(
    cash: Decimal,
    total_shares: Decimal,
    unit_nav: Decimal,
    amount: Decimal,
) -> LedgerState:
    if amount <= 0:
        raise ValueError("subscription amount must be positive")
    if unit_nav <= 0:
        raise ValueError("unit nav must be positive")

    new_shares = quantize_shares(amount / unit_nav)
    return LedgerState(
        cash=quantize_money(cash + amount),
        total_shares=quantize_shares(total_shares + new_shares),
    )


def apply_buy_trade(
    cash: Decimal,
    total_shares: Decimal,
    gross_amount: Decimal,
    fee: Decimal,
) -> LedgerState:
    if gross_amount <= 0:
        raise ValueError("buy amount must be positive")
    if fee < 0:
        raise ValueError("fee cannot be negative")

    cash_after = cash - gross_amount - fee
    if cash_after < 0:
        raise ValueError("cash cannot be negative after buy")
    return LedgerState(cash=quantize_money(cash_after), total_shares=total_shares)


def calculate_unit_nav(total_assets: Decimal, total_shares: Decimal) -> Decimal:
    if total_shares == 0:
        return Decimal("1.0000")
    if total_shares < 0:
        raise ValueError("total shares cannot be negative")
    return quantize_nav(total_assets / total_shares)
