from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.api import alerts, ledger, products, valuation

router = APIRouter()
router.include_router(products.router)
router.include_router(ledger.router)
router.include_router(valuation.router)
router.include_router(alerts.router)


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <!doctype html>
    <html lang="zh-CN">
      <head><title>小满理财</title></head>
      <body><h1>小满理财</h1><p>家庭基金量化系统</p></body>
    </html>
    """
