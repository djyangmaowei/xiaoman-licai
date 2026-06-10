from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.ledger import quantize_money
from app.db.session import SessionLocal
from app.models.ledger import Trade
from app.models.market_data import PricePoint
from app.models.product import Product
from app.models.valuation import DailyValuation
from app.services.portfolio_service import snapshot_portfolio
from app.services.price_service import PriceFetchResult, fetch_eastmoney_price


ProductFetcher = Callable[[Product, date], PriceFetchResult]


@dataclass(frozen=True)
class PriceUpdateSummary:
    target_date: date
    attempted: int
    succeeded: int
    failed: int
    results: list[PriceFetchResult]


def _default_target_date() -> date:
    return date.today() - timedelta(days=1)


def _held_products(db: Session) -> list[Product]:
    rows = (
        db.query(Product)
        .join(Trade, Trade.product_id == Product.id)
        .group_by(Product.id)
        .having(func.coalesce(func.sum(Trade.quantity), 0) != 0)
        .order_by(Product.id)
        .all()
    )
    return list(rows)


def _fetch_product_price(product: Product, target_date: date) -> PriceFetchResult:
    return fetch_eastmoney_price(product.code, target_date, product.channel)


def _record_price_result(db: Session, product: Product, result: PriceFetchResult) -> None:
    price_date = date.fromisoformat(result.price_date)
    price_point = (
        db.query(PricePoint)
        .filter(
            PricePoint.product_id == product.id,
            PricePoint.price_date == price_date,
            PricePoint.source == result.source,
        )
        .first()
    )
    if price_point is None:
        price_point = PricePoint(product_id=product.id, price_date=price_date, source=result.source)
        db.add(price_point)
    price_point.price = result.price
    price_point.status = result.status
    price_point.error_message = result.error_message


def _upsert_daily_valuation(db: Session, valuation_date: date) -> None:
    snapshot = snapshot_portfolio(db)
    valuation = db.query(DailyValuation).filter(DailyValuation.valuation_date == valuation_date).first()
    if valuation is None:
        valuation = DailyValuation(
            valuation_date=valuation_date,
            cash=snapshot.cash,
            total_assets=snapshot.total_assets,
            total_shares=snapshot.total_shares,
            unit_nav=snapshot.unit_nav,
        )
        db.add(valuation)
        return
    valuation.cash = snapshot.cash
    valuation.total_assets = quantize_money(snapshot.total_assets)
    valuation.total_shares = snapshot.total_shares
    valuation.unit_nav = snapshot.unit_nav


def run_price_update(
    target_date: date | None = None,
    db: Session | None = None,
    fetcher: ProductFetcher | None = None,
) -> PriceUpdateSummary:
    should_close = db is None
    session = db or SessionLocal()
    actual_date = target_date or _default_target_date()
    product_fetcher = fetcher or _fetch_product_price
    results: list[PriceFetchResult] = []
    try:
        for product in _held_products(session):
            result = product_fetcher(product, actual_date)
            _record_price_result(session, product, result)
            results.append(result)
        _upsert_daily_valuation(session, actual_date)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if should_close:
            session.close()

    succeeded = len([result for result in results if result.status == "success"])
    return PriceUpdateSummary(
        target_date=actual_date,
        attempted=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


if __name__ == "__main__":
    attempted = run_price_update()
    print(f"attempted={attempted.attempted} succeeded={attempted.succeeded} failed={attempted.failed}")
