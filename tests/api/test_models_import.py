from importlib import import_module

from app.db.base import Base


def test_models_register_tables():
    for module_name in (
        "app.models.alert",
        "app.models.ledger",
        "app.models.market_data",
        "app.models.product",
        "app.models.user",
        "app.models.valuation",
    ):
        import_module(module_name)

    assert "users" in Base.metadata.tables
    assert "products" in Base.metadata.tables
    assert "fund_flows" in Base.metadata.tables
    assert "trades" in Base.metadata.tables
    assert "price_points" in Base.metadata.tables
    assert "daily_valuations" in Base.metadata.tables
    assert "alerts" in Base.metadata.tables
