from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PriceFetchResult:
    code: str
    price_date: str
    price: Decimal | None
    source: str
    status: str
    error_message: str | None


PriceFetcher = Callable[[str], PriceFetchResult]


def select_latest_successful_price(
    results: list[PriceFetchResult],
) -> PriceFetchResult | None:
    successful = [result for result in results if result.status == "success" and result.price is not None]
    if not successful:
        return None
    return max(successful, key=lambda result: result.price_date)


def update_prices_for_codes(codes: list[str], fetcher: PriceFetcher) -> list[PriceFetchResult]:
    return [fetcher(code) for code in codes]
