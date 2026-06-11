from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import create_app
from app.models.market_data import PricePoint


def test_submit_ledger_entry_updates_dashboard_and_holdings():
    client = TestClient(create_app())
    client.get("/")

    response = client.post(
        "/ledger",
        data={
            "trade_date": "2026-06-10",
            "product_id": "1",
            "amount": "10000",
            "price": "1.0000",
            "fee": "0",
            "note": "测试建仓",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    dashboard = client.get("/")
    assert "¥10,000.00" in dashboard.text
    assert "10,000.0000" in dashboard.text

    holdings = client.get("/holdings")
    assert "平安中短债债券A" in holdings.text
    assert "004827" in holdings.text


def test_dashboard_shows_fund_level_profit_metrics():
    client = TestClient(create_app())

    client.post(
        "/ledger",
        data={
            "trade_date": "2026-06-10",
            "product_id": "1",
            "amount": "10000",
            "price": "1.0000",
            "fee": "0",
            "note": "收益展示测试",
        },
        follow_redirects=False,
    )
    with SessionLocal() as db:
        db.add(
            PricePoint(
                product_id=1,
                price_date=date(2026, 6, 11),
                price=Decimal("1.1000"),
                source="test-price",
                status="success",
                error_message=None,
            )
        )
        db.commit()

    dashboard = client.get("/")

    assert "累计投入" in dashboard.text
    assert "累计收益" in dashboard.text
    assert "累计收益率" in dashboard.text
    assert "¥1,000.00" in dashboard.text
    assert "10.00%" in dashboard.text


def test_dashboard_shows_holding_daily_change_attribution():
    client = TestClient(create_app())

    client.post(
        "/ledger",
        data={
            "trade_date": "2026-06-10",
            "product_id": "1",
            "amount": "10000",
            "price": "1.0000",
            "fee": "0",
            "note": "日涨跌归因测试",
        },
        follow_redirects=False,
    )
    with SessionLocal() as db:
        db.add(
            PricePoint(
                product_id=1,
                price_date=date(2026, 6, 11),
                price=Decimal("0.9000"),
                source="test-price",
                status="success",
                error_message=None,
            )
        )
        db.commit()

    dashboard = client.get("/")

    assert "持仓日变动合计" in dashboard.text
    assert "日涨跌 -10.00% / ¥-1,000.00" in dashboard.text

    holdings = client.get("/holdings")
    assert "持仓日变动合计" in holdings.text
    assert "¥-1,000.00" in holdings.text


def test_submit_new_product_creates_product_and_reuses_it_in_list():
    client = TestClient(create_app())

    response = client.post(
        "/ledger",
        data={
            "trade_date": "2026-06-10",
            "new_asset_class": "白酒个股",
            "new_product_name": "贵州茅台",
            "new_product_code": "600519",
            "new_channel": "stock",
            "amount": "20000",
            "price": "1600.0000",
            "fee": "5",
            "note": "手动新增产品测试",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    holdings = client.get("/holdings")
    assert "贵州茅台" in holdings.text
    assert "600519" in holdings.text

    ledger = client.get("/ledger")
    assert "白酒个股 · 贵州茅台 · 600519" in ledger.text


def test_edit_ledger_entry_recalculates_holdings_and_shares():
    client = TestClient(create_app())

    response = client.post(
        "/ledger",
        data={
            "trade_date": "2026-06-10",
            "product_id": "1",
            "amount": "10000",
            "price": "1.0000",
            "fee": "0",
            "note": "录错待修改",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    ledger = client.get("/ledger")
    assert "/ledger/trades/1/edit" in ledger.text

    edit_page = client.get("/ledger/trades/1/edit")
    assert "编辑买入流水" in edit_page.text
    assert "录错待修改" in edit_page.text

    update_response = client.post(
        "/ledger/trades/1/edit",
        data={
            "trade_date": "2026-06-10",
            "product_id": "1",
            "amount": "12000",
            "price": "2.0000",
            "fee": "0",
            "note": "已修正",
        },
        follow_redirects=False,
    )
    assert update_response.status_code == 303

    dashboard = client.get("/")
    assert "¥12,000.00" in dashboard.text
    assert "12,000.0000" in dashboard.text

    holdings = client.get("/holdings")
    assert "6,000.0000" in holdings.text
    assert "¥12,000.00" in holdings.text


def test_sell_ledger_entry_moves_proceeds_to_cash_and_reduces_holding():
    client = TestClient(create_app())

    buy_response = client.post(
        "/ledger",
        data={
            "trade_date": "2026-06-10",
            "product_id": "1",
            "amount": "10000",
            "price": "1.0000",
            "fee": "0",
            "note": "买入后卖出测试",
        },
        follow_redirects=False,
    )
    assert buy_response.status_code == 303

    sell_response = client.post(
        "/ledger/sell",
        data={
            "trade_date": "2026-06-11",
            "product_id": "1",
            "amount": "3000",
            "price": "1.0000",
            "fee": "10",
            "note": "部分卖出",
        },
        follow_redirects=False,
    )
    assert sell_response.status_code == 303

    dashboard = client.get("/")
    assert "¥2,990.00" in dashboard.text
    assert "10,000.0000" in dashboard.text

    holdings = client.get("/holdings")
    assert "7,000.0000" in holdings.text
    assert "¥7,000.00" in holdings.text

    ledger = client.get("/ledger")
    assert "卖出" in ledger.text
    assert "部分卖出" in ledger.text


def test_edit_sell_entry_recalculates_cash_and_holding():
    client = TestClient(create_app())

    client.post(
        "/ledger",
        data={
            "trade_date": "2026-06-10",
            "product_id": "1",
            "amount": "10000",
            "price": "1.0000",
            "fee": "0",
            "note": "买入",
        },
        follow_redirects=False,
    )
    client.post(
        "/ledger/sell",
        data={
            "trade_date": "2026-06-11",
            "product_id": "1",
            "amount": "3000",
            "price": "1.0000",
            "fee": "10",
            "note": "卖出录错",
        },
        follow_redirects=False,
    )

    edit_page = client.get("/ledger/trades/2/edit")
    assert "编辑卖出流水" in edit_page.text

    update_response = client.post(
        "/ledger/trades/2/edit",
        data={
            "trade_date": "2026-06-11",
            "product_id": "1",
            "amount": "2000",
            "price": "1.0000",
            "fee": "5",
            "note": "卖出修正",
        },
        follow_redirects=False,
    )
    assert update_response.status_code == 303

    dashboard = client.get("/")
    assert "¥1,995.00" in dashboard.text

    holdings = client.get("/holdings")
    assert "8,000.0000" in holdings.text
