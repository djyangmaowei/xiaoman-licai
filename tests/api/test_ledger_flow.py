from fastapi.testclient import TestClient

from app.main import create_app


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
