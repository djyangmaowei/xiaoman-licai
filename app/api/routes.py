from datetime import date
from decimal import Decimal

from fastapi import APIRouter
from fastapi import Depends, Form
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api import alerts, ledger, products, valuation
from app.db.session import get_db
from app.services.portfolio_service import create_combined_buy, snapshot_portfolio
from app.services.product_service import list_active_products
from app.ui.formatters import money, number4, percent

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["money"] = money
templates.env.filters["number4"] = number4
templates.env.filters["percent"] = percent
router.include_router(products.router)
router.include_router(ledger.router)
router.include_router(valuation.router)
router.include_router(alerts.router)


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    snapshot = snapshot_portfolio(db)
    return templates.TemplateResponse(request, "dashboard.html", {"snapshot": snapshot})


@router.get("/holdings")
def holdings(request: Request, db: Session = Depends(get_db)):
    snapshot = snapshot_portfolio(db)
    return templates.TemplateResponse(request, "holdings.html", {"snapshot": snapshot})


@router.get("/ledger")
def ledger_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "ledger.html",
        {
            "products": list_active_products(db),
            "today": date.today().isoformat(),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/ledger")
def submit_ledger_entry(
    trade_date: date = Form(...),
    product_id: int = Form(...),
    amount: Decimal = Form(...),
    price: Decimal = Form(...),
    fee: Decimal = Form(Decimal("0")),
    use_existing_cash: bool = Form(False),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        create_combined_buy(
            db=db,
            trade_date=trade_date,
            product_id=product_id,
            amount=amount,
            price=price,
            fee=fee,
            use_existing_cash=use_existing_cash,
            note=note,
        )
    except ValueError as exc:
        return RedirectResponse(f"/ledger?error={str(exc)}", status_code=303)
    return RedirectResponse("/", status_code=303)


@router.get("/updates")
def updates(request: Request):
    return templates.TemplateResponse(request, "updates.html")


@router.get("/alerts")
def alerts_page(request: Request):
    return templates.TemplateResponse(request, "alerts.html")
