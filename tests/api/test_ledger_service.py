from decimal import Decimal

from app.schemas.ledger import CombinedBuyInstruction
from app.services.ledger_service import prepare_combined_buy_entries


def test_combined_buy_instruction_creates_subscription_and_buy_draft():
    draft = prepare_combined_buy_entries(
        CombinedBuyInstruction(
            trade_date="2026-06-10",
            amount=Decimal("10000"),
            product_name="华安黄金ETF",
            product_code="518880",
            unit_nav=Decimal("1.0000"),
            price=Decimal("5.000"),
            fee=Decimal("1.00"),
            use_existing_cash=False,
        )
    )

    assert len(draft.entries) == 2
    assert draft.entries[0].entry_type == "SUBSCRIBE"
    assert draft.entries[0].shares_delta == Decimal("10000.0000")
    assert draft.entries[1].entry_type == "BUY"
    assert draft.entries[1].quantity == Decimal("1999.8000")


def test_existing_cash_buy_creates_only_buy_draft():
    draft = prepare_combined_buy_entries(
        CombinedBuyInstruction(
            trade_date="2026-06-10",
            amount=Decimal("10000"),
            product_name="华安黄金ETF",
            product_code="518880",
            unit_nav=Decimal("1.0000"),
            price=Decimal("5.000"),
            fee=Decimal("0.00"),
            use_existing_cash=True,
        )
    )

    assert [entry.entry_type for entry in draft.entries] == ["BUY"]
