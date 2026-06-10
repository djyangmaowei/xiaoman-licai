from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.jobs.update_prices import run_price_update
from app.main import create_app
from app.models.market_data import PricePoint
from app.services.portfolio_service import create_combined_buy
from app.services.price_service import PriceFetchResult, select_latest_successful_price


def test_latest_successful_price_ignores_failed_result():
    result = select_latest_successful_price(
        [
            PriceFetchResult("518880", "2026-06-09", Decimal("5.10"), "eastmoney", "success", None),
            PriceFetchResult("518880", "2026-06-10", None, "eastmoney", "failed", "not disclosed"),
        ]
    )

    assert result is not None
    assert result.price == Decimal("5.10")
    assert result.price_date == "2026-06-09"


def test_price_update_records_prices_and_valuation():
    create_app()

    with SessionLocal() as db:
        create_combined_buy(
            db=db,
            trade_date=date(2026, 6, 9),
            product_id=1,
            amount=Decimal("10000"),
            price=Decimal("1.0000"),
            fee=Decimal("0"),
            use_existing_cash=False,
            note="价格更新测试",
        )

        def fake_fetcher(product, target_date):
            return PriceFetchResult(
                code=product.code,
                price_date=target_date.isoformat(),
                price=Decimal("1.1000"),
                source="fake-source",
                status="success",
                error_message=None,
            )

        summary = run_price_update(target_date=date(2026, 6, 10), db=db, fetcher=fake_fetcher)

        point = db.query(PricePoint).filter(PricePoint.source == "fake-source").one()
        assert summary.attempted == 1
        assert summary.succeeded == 1
        assert point.price == Decimal("1.1000")


def test_updates_page_contains_manual_run_form():
    client = TestClient(create_app())

    response = client.get("/updates")

    assert response.status_code == 200
    assert "更新 T+1 数据" in response.text
    assert "/updates/run" in response.text
