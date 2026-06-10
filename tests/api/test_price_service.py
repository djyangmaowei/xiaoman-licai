from decimal import Decimal

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
