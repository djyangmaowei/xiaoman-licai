from decimal import Decimal

from fastapi import APIRouter

router = APIRouter(prefix="/api/products", tags=["products"])


SEED_PRODUCTS = [
    {
        "asset_class": "债券",
        "target_weight": Decimal("0.25"),
        "name": "平安中短债债券A",
        "codes": ["004827"],
    },
    {
        "asset_class": "红利低波",
        "target_weight": Decimal("0.10"),
        "name": "南方标普中国A股大盘红利低波50ETF / 场外A",
        "codes": ["515450", "008163"],
    },
    {
        "asset_class": "宽基",
        "target_weight": Decimal("0.30"),
        "name": "华泰柏瑞中证A500ETF / 场外A",
        "codes": ["563360", "022438"],
    },
    {
        "asset_class": "科技轮动",
        "target_weight": Decimal("0.15"),
        "name": "易方达中证科技50ETF / 场外A",
        "codes": ["159807", "012450"],
    },
    {
        "asset_class": "海外大盘",
        "target_weight": Decimal("0.10"),
        "name": "博时标普500ETF / 场外A",
        "codes": ["513500", "050025"],
    },
    {
        "asset_class": "黄金",
        "target_weight": Decimal("0.10"),
        "name": "华安黄金ETF / 场外A",
        "codes": ["518880", "000216"],
    },
]


@router.get("/seed")
def list_seed_products():
    return SEED_PRODUCTS
