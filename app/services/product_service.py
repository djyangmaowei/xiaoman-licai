from decimal import Decimal

from sqlalchemy.orm import Session

from app.api.products import SEED_PRODUCTS
from app.models.product import Product


def seed_products(db: Session) -> None:
    if db.query(Product).first() is not None:
        return

    for seed in SEED_PRODUCTS:
        codes = seed["codes"]
        for index, code in enumerate(codes):
            channel = "exchange" if code.startswith(("51", "56", "15")) else "otc"
            name = seed["name"] if index == 0 else f"{seed['name']}（场外）"
            db.add(
                Product(
                    asset_class=seed["asset_class"],
                    name=name,
                    code=code,
                    channel=channel,
                    target_weight=Decimal(seed["target_weight"]),
                    is_active=True,
                )
            )
    db.commit()


def list_active_products(db: Session) -> list[Product]:
    return db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.id).all()
