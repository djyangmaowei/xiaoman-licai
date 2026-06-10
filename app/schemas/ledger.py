from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CombinedBuyInstruction(BaseModel):
    trade_date: str
    amount: Decimal = Field(gt=Decimal("0"))
    product_name: str
    product_code: str
    unit_nav: Decimal = Field(gt=Decimal("0"))
    price: Decimal = Field(gt=Decimal("0"))
    fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    use_existing_cash: bool = False


class LedgerDraftEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    entry_type: str
    trade_date: str
    amount: Decimal
    product_name: str | None = None
    product_code: str | None = None
    unit_nav: Decimal | None = None
    shares_delta: Decimal | None = None
    price: Decimal | None = None
    quantity: Decimal | None = None
    fee: Decimal = Decimal("0.00")
    note: str | None = None


class LedgerDraft(BaseModel):
    entries: list[LedgerDraftEntry]
