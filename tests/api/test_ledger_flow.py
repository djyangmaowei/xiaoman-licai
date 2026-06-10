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
