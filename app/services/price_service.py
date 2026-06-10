from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import json
import re
import subprocess
from urllib.parse import urlencode

import httpx


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


def _read_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 XiaomanLicai/1.0",
        "Referer": "https://fund.eastmoney.com/",
    }
    try:
        with httpx.Client(headers=headers, timeout=12) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError:
        completed = subprocess.run(
            ["curl", "-4", "-sS", "-A", headers["User-Agent"], "-e", headers["Referer"], url],
            check=True,
            capture_output=True,
            text=True,
            timeout=12,
        )
        return completed.stdout


def _stock_market_prefix(code: str) -> str:
    return "0" if code.startswith(("15", "16", "18")) else "1"


def _tencent_symbol(code: str) -> str:
    return f"sz{code}" if code.startswith(("15", "16", "18")) else f"sh{code}"


def fetch_eastmoney_exchange_close(code: str, target_date: date) -> PriceFetchResult:
    compact_date = target_date.strftime("%Y%m%d")
    params = urlencode(
        {
            "secid": f"{_stock_market_prefix(code)}.{code}",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": compact_date,
            "end": compact_date,
            "lmt": "1",
        }
    )
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?{params}"
    try:
        payload = json.loads(_read_url(url))
        klines = (payload.get("data") or {}).get("klines") or []
        if not klines:
            return PriceFetchResult(code, target_date.isoformat(), None, "eastmoney-kline", "failed", "no kline")
        fields = klines[0].split(",")
        return PriceFetchResult(code, fields[0], Decimal(fields[2]), "eastmoney-kline", "success", None)
    except Exception as exc:
        return PriceFetchResult(code, target_date.isoformat(), None, "eastmoney-kline", "failed", str(exc))


def fetch_tencent_exchange_close(code: str, target_date: date) -> PriceFetchResult:
    day = target_date.isoformat()
    symbol = _tencent_symbol(code)
    params = urlencode({"param": f"{symbol},day,{day},{day},1,qfq"})
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?{params}"
    try:
        payload = json.loads(_read_url(url))
        product_data = (payload.get("data") or {}).get(symbol) or {}
        rows = product_data.get("qfqday") or product_data.get("day") or []
        if not rows:
            return PriceFetchResult(code, day, None, "tencent-kline", "failed", "no kline")
        row = rows[0]
        return PriceFetchResult(code, row[0], Decimal(row[2]), "tencent-kline", "success", None)
    except Exception as exc:
        return PriceFetchResult(code, day, None, "tencent-kline", "failed", str(exc))


def fetch_eastmoney_fund_nav(code: str, target_date: date) -> PriceFetchResult:
    day = target_date.isoformat()
    params = urlencode({"type": "lsjz", "code": code, "sdate": day, "edate": day, "per": "20"})
    url = f"https://fundf10.eastmoney.com/F10DataApi.aspx?{params}"
    try:
        html = _read_url(url)
        match = re.search(r"<td>(\d{4}-\d{2}-\d{2})</td><td class='tor bold'>([0-9.]+)</td>", html)
        if match is None:
            return PriceFetchResult(code, day, None, "eastmoney-fund-nav", "failed", "no nav")
        return PriceFetchResult(code, match.group(1), Decimal(match.group(2)), "eastmoney-fund-nav", "success", None)
    except Exception as exc:
        return PriceFetchResult(code, day, None, "eastmoney-fund-nav", "failed", str(exc))


def fetch_eastmoney_price(code: str, target_date: date, channel: str) -> PriceFetchResult:
    if channel == "exchange":
        result = fetch_eastmoney_exchange_close(code, target_date)
        if result.status == "success":
            return result
        result = fetch_tencent_exchange_close(code, target_date)
        if result.status == "success":
            return result
    return fetch_eastmoney_fund_nav(code, target_date)
