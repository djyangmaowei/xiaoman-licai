from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from app.api import alerts, ledger, products, valuation

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
router.include_router(products.router)
router.include_router(ledger.router)
router.include_router(valuation.router)
router.include_router(alerts.router)


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@router.get("/holdings")
def holdings(request: Request):
    return templates.TemplateResponse(request, "holdings.html")


@router.get("/ledger")
def ledger_page(request: Request):
    return templates.TemplateResponse(request, "ledger.html")


@router.get("/updates")
def updates(request: Request):
    return templates.TemplateResponse(request, "updates.html")


@router.get("/alerts")
def alerts_page(request: Request):
    return templates.TemplateResponse(request, "alerts.html")
