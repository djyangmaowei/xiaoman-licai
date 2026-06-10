from fastapi.testclient import TestClient

from app.main import create_app


def test_dashboard_contains_core_nav_items():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "小满理财" in response.text
    assert "总览" in response.text
    assert "持仓" in response.text
    assert "流水" in response.text
    assert "预警" in response.text
