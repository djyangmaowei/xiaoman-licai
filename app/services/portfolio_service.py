from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.ledger import calculate_unit_nav, quantize_money, quantize_nav, quantize_shares
from app.models.ledger import FundFlow, Trade
from app.models.market_data import PricePoint
from app.models.product import Product
from app.models.valuation import DailyValuation


@dataclass(frozen=True)
class HoldingRow:
    product: Product
    quantity: Decimal
    cost: Decimal
    price: Decimal
    market_value: Decimal
    weight: Decimal
    target_weight: Decimal
    profit: Decimal


@dataclass(frozen=True)
class PortfolioSnapshot:
    as_of_date: date
    cash: Decimal
    total_shares: Decimal
    total_assets: Decimal
    unit_nav: Decimal
    invested_capital: Decimal
    total_profit: Decimal
    unit_nav_change: Decimal
    holdings: list[HoldingRow]


@dataclass(frozen=True)
class LedgerEntry:
    trade: Trade
    product: Product
    uses_existing_cash: bool


def current_unit_nav(db: Session) -> Decimal:
    latest = db.query(DailyValuation).order_by(DailyValuation.valuation_date.desc()).first()
    return latest.unit_nav if latest else Decimal("1.0000")


def _total_fund_shares(db: Session) -> Decimal:
    total = db.query(func.coalesce(func.sum(FundFlow.shares_delta), 0)).scalar()
    return quantize_shares(Decimal(total))


def _cash_balance(db: Session) -> Decimal:
    flow_cash = db.query(func.coalesce(func.sum(FundFlow.amount), 0)).scalar()
    buy_cash = db.query(func.coalesce(func.sum(Trade.amount + Trade.fee), 0)).filter(
        Trade.trade_type == "BUY"
    ).scalar()
    sell_cash = db.query(func.coalesce(func.sum(Trade.amount - Trade.fee), 0)).filter(
        Trade.trade_type == "SELL"
    ).scalar()
    return quantize_money(Decimal(flow_cash) - Decimal(buy_cash) + Decimal(sell_cash))


def _invested_capital(db: Session) -> Decimal:
    total = db.query(func.coalesce(func.sum(FundFlow.amount), 0)).scalar()
    return quantize_money(Decimal(total))


def _snapshot_date(db: Session) -> date:
    latest = db.query(DailyValuation).order_by(DailyValuation.valuation_date.desc()).first()
    return latest.valuation_date if latest else date.today()


def _latest_price(db: Session, product_id: int, fallback: Decimal) -> Decimal:
    price = (
        db.query(PricePoint)
        .filter(PricePoint.product_id == product_id, PricePoint.status == "success")
        .order_by(PricePoint.price_date.desc(), PricePoint.id.desc())
        .first()
    )
    return price.price if price and price.price is not None else fallback


def _position_quantity(db: Session, product_id: int) -> Decimal:
    quantity = db.query(func.coalesce(func.sum(Trade.quantity), 0)).filter(
        Trade.product_id == product_id
    ).scalar()
    return quantize_shares(Decimal(quantity))


def _position_cost(db: Session, product_id: int, quantity: Decimal) -> Decimal:
    buy_quantity = db.query(func.coalesce(func.sum(Trade.quantity), 0)).filter(
        Trade.product_id == product_id,
        Trade.trade_type == "BUY",
    ).scalar()
    buy_quantity = quantize_shares(Decimal(buy_quantity))
    if buy_quantity <= 0 or quantity <= 0:
        return Decimal("0.00")

    buy_cost = db.query(func.coalesce(func.sum(Trade.amount), 0)).filter(
        Trade.product_id == product_id,
        Trade.trade_type == "BUY",
    ).scalar()
    average_cost = Decimal(buy_cost) / buy_quantity
    return quantize_money(average_cost * quantity)


def _matching_fund_flow(db: Session, trade: Trade) -> FundFlow | None:
    if trade.trade_type != "BUY":
        return None
    return (
        db.query(FundFlow)
        .filter(
            FundFlow.flow_type == "SUBSCRIBE",
            FundFlow.trade_date == trade.trade_date,
            FundFlow.amount == trade.amount,
            FundFlow.note == (trade.note or f"外部投入并买入 {db.get(Product, trade.product_id).name}"),
        )
        .order_by(FundFlow.id.desc())
        .first()
    )


def _upsert_valuation(db: Session, valuation_date: date) -> None:
    snapshot = snapshot_portfolio(db)
    valuation = db.query(DailyValuation).filter(DailyValuation.valuation_date == valuation_date).first()
    if valuation is None:
        db.add(
            DailyValuation(
                valuation_date=valuation_date,
                cash=snapshot.cash,
                total_assets=snapshot.total_assets,
                total_shares=snapshot.total_shares,
                unit_nav=snapshot.unit_nav,
            )
        )
    else:
        valuation.cash = snapshot.cash
        valuation.total_assets = snapshot.total_assets
        valuation.total_shares = snapshot.total_shares
        valuation.unit_nav = snapshot.unit_nav


def snapshot_portfolio(db: Session) -> PortfolioSnapshot:
    cash = _cash_balance(db)
    total_shares = _total_fund_shares(db)
    invested_capital = _invested_capital(db)
    holdings: list[HoldingRow] = []

    products = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id).all()
    for product in products:
        quantity = _position_quantity(db, product.id)
        if quantity == 0:
            continue

        cost = _position_cost(db, product.id, quantity)
        fallback_price = cost / quantity if quantity else Decimal("0")
        price = _latest_price(db, product.id, fallback_price)
        market_value = quantize_money(quantity * price)
        holdings.append(
            HoldingRow(
                product=product,
                quantity=quantity,
                cost=cost,
                price=price,
                market_value=market_value,
                weight=Decimal("0"),
                target_weight=product.target_weight,
                profit=quantize_money(market_value - cost),
            )
        )

    total_assets = quantize_money(cash + sum((row.market_value for row in holdings), Decimal("0")))
    unit_nav = calculate_unit_nav(total_assets, total_shares)
    weighted_holdings = [
        HoldingRow(
            product=row.product,
            quantity=row.quantity,
            cost=row.cost,
            price=row.price,
            market_value=row.market_value,
            weight=quantize_nav(row.market_value / total_assets) if total_assets else Decimal("0.0000"),
            target_weight=row.target_weight,
            profit=row.profit,
        )
        for row in holdings
    ]
    return PortfolioSnapshot(
        as_of_date=_snapshot_date(db),
        cash=cash,
        total_shares=total_shares,
        total_assets=total_assets,
        unit_nav=unit_nav,
        invested_capital=invested_capital,
        total_profit=quantize_money(total_assets - invested_capital),
        unit_nav_change=quantize_nav(unit_nav - Decimal("1.0000")),
        holdings=weighted_holdings,
    )


def list_recent_ledger_entries(db: Session, limit: int = 20) -> list[LedgerEntry]:
    trades = db.query(Trade).order_by(Trade.trade_date.desc(), Trade.id.desc()).limit(limit).all()
    entries: list[LedgerEntry] = []
    for trade in trades:
        product = db.get(Product, trade.product_id)
        if product is None:
            continue
        entries.append(
            LedgerEntry(
                trade=trade,
                product=product,
                uses_existing_cash=_matching_fund_flow(db, trade) is None,
            )
        )
    return entries


def get_ledger_entry(db: Session, trade_id: int) -> LedgerEntry | None:
    trade = db.get(Trade, trade_id)
    if trade is None:
        return None
    product = db.get(Product, trade.product_id)
    if product is None:
        return None
    return LedgerEntry(
        trade=trade,
        product=product,
        uses_existing_cash=_matching_fund_flow(db, trade) is None,
    )


def create_combined_buy(
    db: Session,
    trade_date: date,
    product_id: int,
    amount: Decimal,
    price: Decimal,
    fee: Decimal,
    use_existing_cash: bool,
    note: str | None,
) -> PortfolioSnapshot:
    product = db.get(Product, product_id)
    if product is None:
        raise ValueError("product not found")
    if amount <= 0 or price <= 0 or fee < 0:
        raise ValueError("amount and price must be positive; fee cannot be negative")

    unit_nav = current_unit_nav(db)
    if not use_existing_cash:
        db.add(
            FundFlow(
                flow_type="SUBSCRIBE",
                trade_date=trade_date,
                amount=amount,
                unit_nav=unit_nav,
                shares_delta=quantize_shares(amount / unit_nav),
                note=note or f"外部投入并买入 {product.name}",
            )
        )

    net_amount = amount - fee
    if net_amount <= 0:
        raise ValueError("amount after fee must be positive")
    quantity = quantize_shares(net_amount / price)
    db.add(
        Trade(
            trade_type="BUY",
            trade_date=trade_date,
            product_id=product.id,
            amount=amount,
            quantity=quantity,
            price=price,
            fee=fee,
            note=note,
        )
    )
    db.add(
        PricePoint(
            product_id=product.id,
            price_date=trade_date,
            price=price,
            source="manual-entry",
            status="success",
            error_message=None,
        )
    )
    db.flush()
    snapshot = snapshot_portfolio(db)
    _upsert_valuation(db, trade_date)
    db.commit()
    return snapshot


def create_sell(
    db: Session,
    trade_date: date,
    product_id: int,
    amount: Decimal,
    price: Decimal,
    fee: Decimal,
    note: str | None,
) -> PortfolioSnapshot:
    product = db.get(Product, product_id)
    if product is None:
        raise ValueError("product not found")
    if amount <= 0 or price <= 0 or fee < 0:
        raise ValueError("amount and price must be positive; fee cannot be negative")

    quantity = quantize_shares(amount / price)
    if quantity <= 0:
        raise ValueError("sell quantity must be positive")
    current_quantity = _position_quantity(db, product.id)
    if quantity > current_quantity:
        raise ValueError("sell quantity exceeds current holding")

    db.add(
        Trade(
            trade_type="SELL",
            trade_date=trade_date,
            product_id=product.id,
            amount=amount,
            quantity=-quantity,
            price=price,
            fee=fee,
            note=note,
        )
    )
    db.add(
        PricePoint(
            product_id=product.id,
            price_date=trade_date,
            price=price,
            source="manual-entry",
            status="success",
            error_message=None,
        )
    )
    db.flush()
    snapshot = snapshot_portfolio(db)
    _upsert_valuation(db, trade_date)
    db.commit()
    return snapshot


def update_combined_buy(
    db: Session,
    trade_id: int,
    trade_date: date,
    product_id: int,
    amount: Decimal,
    price: Decimal,
    fee: Decimal,
    use_existing_cash: bool,
    note: str | None,
) -> PortfolioSnapshot:
    trade = db.get(Trade, trade_id)
    product = db.get(Product, product_id)
    if trade is None:
        raise ValueError("trade not found")
    if product is None:
        raise ValueError("product not found")
    if amount <= 0 or price <= 0 or fee < 0:
        raise ValueError("amount and price must be positive; fee cannot be negative")

    old_trade_date = trade.trade_date
    flow = _matching_fund_flow(db, trade)
    if use_existing_cash:
        if flow is not None:
            db.delete(flow)
    else:
        if flow is None:
            unit_nav = current_unit_nav(db)
            flow = FundFlow(
                flow_type="SUBSCRIBE",
                trade_date=trade_date,
                unit_nav=unit_nav,
                amount=amount,
                shares_delta=quantize_shares(amount / unit_nav),
                note=note or f"外部投入并买入 {product.name}",
            )
            db.add(flow)
        else:
            flow.trade_date = trade_date
            flow.amount = amount
            flow.shares_delta = quantize_shares(amount / flow.unit_nav)
            flow.note = note or f"外部投入并买入 {product.name}"

    net_amount = amount - fee
    if net_amount <= 0:
        raise ValueError("amount after fee must be positive")

    price_point = (
        db.query(PricePoint)
        .filter(
            PricePoint.product_id == trade.product_id,
            PricePoint.price_date == trade.trade_date,
            PricePoint.source == "manual-entry",
        )
        .order_by(PricePoint.id.desc())
        .first()
    )
    if price_point is None:
        price_point = PricePoint(
            product_id=product.id,
            price_date=trade_date,
            source="manual-entry",
            status="success",
            error_message=None,
        )
        db.add(price_point)
    price_point.product_id = product.id
    price_point.price_date = trade_date
    price_point.price = price
    price_point.status = "success"
    price_point.error_message = None

    trade.trade_date = trade_date
    trade.product_id = product.id
    trade.amount = amount
    trade.quantity = quantize_shares(net_amount / price)
    trade.price = price
    trade.fee = fee
    trade.note = note

    db.flush()
    snapshot = snapshot_portfolio(db)
    _upsert_valuation(db, old_trade_date)
    _upsert_valuation(db, trade_date)
    db.commit()
    return snapshot


def update_sell(
    db: Session,
    trade_id: int,
    trade_date: date,
    product_id: int,
    amount: Decimal,
    price: Decimal,
    fee: Decimal,
    note: str | None,
) -> PortfolioSnapshot:
    trade = db.get(Trade, trade_id)
    product = db.get(Product, product_id)
    if trade is None:
        raise ValueError("trade not found")
    if trade.trade_type != "SELL":
        raise ValueError("trade is not a sell")
    if product is None:
        raise ValueError("product not found")
    if amount <= 0 or price <= 0 or fee < 0:
        raise ValueError("amount and price must be positive; fee cannot be negative")

    old_trade_date = trade.trade_date
    new_quantity = quantize_shares(amount / price)
    current_quantity_without_trade = _position_quantity(db, product.id)
    if trade.product_id == product.id:
        current_quantity_without_trade -= trade.quantity
    if new_quantity > current_quantity_without_trade:
        raise ValueError("sell quantity exceeds current holding")

    price_point = (
        db.query(PricePoint)
        .filter(
            PricePoint.product_id == trade.product_id,
            PricePoint.price_date == trade.trade_date,
            PricePoint.source == "manual-entry",
        )
        .order_by(PricePoint.id.desc())
        .first()
    )
    if price_point is None:
        price_point = PricePoint(
            product_id=product.id,
            price_date=trade_date,
            source="manual-entry",
            status="success",
            error_message=None,
        )
        db.add(price_point)
    price_point.product_id = product.id
    price_point.price_date = trade_date
    price_point.price = price
    price_point.status = "success"
    price_point.error_message = None

    trade.trade_date = trade_date
    trade.product_id = product.id
    trade.amount = amount
    trade.quantity = -new_quantity
    trade.price = price
    trade.fee = fee
    trade.note = note

    db.flush()
    snapshot = snapshot_portfolio(db)
    _upsert_valuation(db, old_trade_date)
    _upsert_valuation(db, trade_date)
    db.commit()
    return snapshot
