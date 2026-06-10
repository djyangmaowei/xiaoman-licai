from app.domain.ledger import quantize_shares
from app.schemas.ledger import CombinedBuyInstruction, LedgerDraft, LedgerDraftEntry


def prepare_combined_buy_entries(instruction: CombinedBuyInstruction) -> LedgerDraft:
    entries: list[LedgerDraftEntry] = []

    if not instruction.use_existing_cash:
        entries.append(
            LedgerDraftEntry(
                entry_type="SUBSCRIBE",
                trade_date=instruction.trade_date,
                amount=instruction.amount,
                unit_nav=instruction.unit_nav,
                shares_delta=quantize_shares(instruction.amount / instruction.unit_nav),
                note="外部资金投入",
            )
        )

    net_buy_amount = instruction.amount - instruction.fee
    if net_buy_amount <= 0:
        raise ValueError("buy amount after fee must be positive")

    entries.append(
        LedgerDraftEntry(
            entry_type="BUY",
            trade_date=instruction.trade_date,
            amount=instruction.amount,
            product_name=instruction.product_name,
            product_code=instruction.product_code,
            price=instruction.price,
            quantity=quantize_shares(net_buy_amount / instruction.price),
            fee=instruction.fee,
            note="内部产品买入",
        )
    )

    return LedgerDraft(entries=entries)
