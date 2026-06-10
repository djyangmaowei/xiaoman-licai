from fastapi.testclient import TestClient

from app.main import create_app


def test_home_page_contains_brand_name():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "小满理财" in response.text


def test_api_product_config_lists_seed_assets():
    client = TestClient(create_app())

    response = client.get("/api/products/seed")

    assert response.status_code == 200
    assert response.json()[0]["asset_class"] == "债券"
