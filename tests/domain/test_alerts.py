from decimal import Decimal

from app.domain.alerts import evaluate_weight_alert


def test_weight_alert_triggers_when_deviation_exceeds_threshold():
    alert = evaluate_weight_alert(
        product_code="563360",
        current_weight=Decimal("0.38"),
        target_weight=Decimal("0.30"),
        threshold=Decimal("0.05"),
    )

    assert alert is not None
    assert alert.product_code == "563360"
    assert alert.severity == "warning"


def test_weight_alert_ignores_small_deviation():
    alert = evaluate_weight_alert(
        product_code="563360",
        current_weight=Decimal("0.32"),
        target_weight=Decimal("0.30"),
        threshold=Decimal("0.05"),
    )

    assert alert is None
