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


def find_product_by_code(db: Session, code: str) -> Product | None:
    normalized_code = code.strip()
    if not normalized_code:
        return None
    return db.query(Product).filter(Product.code == normalized_code).first()


def get_or_create_product(
    db: Session,
    asset_class: str,
    name: str,
    code: str,
    channel: str,
) -> Product:
    product = find_product_by_code(db, code)
    if product is not None:
        return product

    if not asset_class.strip() or not name.strip() or not code.strip():
        raise ValueError("new product requires asset class, name, and code")

    product = Product(
        asset_class=asset_class.strip(),
        name=name.strip(),
        code=code.strip(),
        channel=channel.strip() or "manual",
        target_weight=Decimal("0"),
        is_active=True,
    )
    db.add(product)
    db.flush()
    return product
