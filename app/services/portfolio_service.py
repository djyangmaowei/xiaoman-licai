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
    cash: Decimal
    total_shares: Decimal
    total_assets: Decimal
    unit_nav: Decimal
    holdings: list[HoldingRow]


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


def _latest_price(db: Session, product_id: int, fallback: Decimal) -> Decimal:
    price = (
        db.query(PricePoint)
        .filter(PricePoint.product_id == product_id, PricePoint.status == "success")
        .order_by(PricePoint.price_date.desc(), PricePoint.id.desc())
        .first()
    )
    return price.price if price and price.price is not None else fallback


def snapshot_portfolio(db: Session) -> PortfolioSnapshot:
    cash = _cash_balance(db)
    total_shares = _total_fund_shares(db)
    holdings: list[HoldingRow] = []

    products = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id).all()
    for product in products:
        quantity = db.query(func.coalesce(func.sum(Trade.quantity), 0)).filter(
            Trade.product_id == product.id
        ).scalar()
        quantity = quantize_shares(Decimal(quantity))
        if quantity == 0:
            continue

        cost = db.query(func.coalesce(func.sum(Trade.amount + Trade.fee), 0)).filter(
            Trade.product_id == product.id
        ).scalar()
        cost = quantize_money(Decimal(cost))
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
        cash=cash,
        total_shares=total_shares,
        total_assets=total_assets,
        unit_nav=unit_nav,
        holdings=weighted_holdings,
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
    valuation = db.query(DailyValuation).filter(DailyValuation.valuation_date == trade_date).first()
    if valuation is None:
        db.add(
            DailyValuation(
                valuation_date=trade_date,
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
    db.commit()
    return snapshot
