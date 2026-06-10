from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AlertDecision:
    product_code: str
    severity: str
    message: str


def evaluate_weight_alert(
    product_code: str,
    current_weight: Decimal,
    target_weight: Decimal,
    threshold: Decimal,
) -> AlertDecision | None:
    deviation = abs(current_weight - target_weight)
    if deviation <= threshold:
        return None
    return AlertDecision(
        product_code=product_code,
        severity="warning",
        message=f"{product_code} 仓位偏离目标 {deviation:.2%}",
    )
