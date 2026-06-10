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
from app.jobs.update_prices import run_price_update
from app.models.market_data import PricePoint
from app.models.product import Product
from app.services.portfolio_service import (
    create_combined_buy,
    get_ledger_entry,
    list_recent_ledger_entries,
    snapshot_portfolio,
    update_combined_buy,
)
from app.services.product_service import get_or_create_product, list_active_products
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
            "entries": list_recent_ledger_entries(db),
            "today": date.today().isoformat(),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/ledger")
def submit_ledger_entry(
    trade_date: date = Form(...),
    product_id: int | None = Form(None),
    new_product_name: str | None = Form(None),
    new_product_code: str | None = Form(None),
    new_asset_class: str | None = Form(None),
    new_channel: str = Form("manual"),
    amount: Decimal = Form(...),
    price: Decimal = Form(...),
    fee: Decimal = Form(Decimal("0")),
    use_existing_cash: bool = Form(False),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        if new_product_code and new_product_name and new_asset_class:
            product = get_or_create_product(
                db=db,
                asset_class=new_asset_class,
                name=new_product_name,
                code=new_product_code,
                channel=new_channel,
            )
            product_id = product.id
        if product_id is None:
            raise ValueError("please select an existing product or enter a new product")
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


@router.get("/ledger/trades/{trade_id}/edit")
def edit_ledger_entry(trade_id: int, request: Request, db: Session = Depends(get_db)):
    entry = get_ledger_entry(db, trade_id)
    if entry is None:
        return RedirectResponse("/ledger?error=trade not found", status_code=303)
    return templates.TemplateResponse(
        request,
        "ledger_edit.html",
        {
            "entry": entry,
            "products": list_active_products(db),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/ledger/trades/{trade_id}/edit")
def update_ledger_entry(
    trade_id: int,
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
        update_combined_buy(
            db=db,
            trade_id=trade_id,
            trade_date=trade_date,
            product_id=product_id,
            amount=amount,
            price=price,
            fee=fee,
            use_existing_cash=use_existing_cash,
            note=note,
        )
    except ValueError as exc:
        return RedirectResponse(f"/ledger/trades/{trade_id}/edit?error={str(exc)}", status_code=303)
    return RedirectResponse("/ledger", status_code=303)


@router.get("/updates")
def updates(request: Request, db: Session = Depends(get_db)):
    raw_price_rows = (
        db.query(PricePoint, Product)
        .join(Product, Product.id == PricePoint.product_id)
        .order_by(PricePoint.price_date.desc(), PricePoint.id.desc())
        .limit(100)
        .all()
    )
    price_rows = []
    seen_product_ids: set[int] = set()
    for point, product in raw_price_rows:
        if product.id in seen_product_ids:
            continue
        seen_product_ids.add(product.id)
        price_rows.append((point, product))
    return templates.TemplateResponse(
        request,
        "updates.html",
        {
            "price_rows": price_rows,
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/updates/run")
def run_updates(target_date: str | None = Form(None), db: Session = Depends(get_db)):
    try:
        parsed_date = date.fromisoformat(target_date) if target_date else None
        summary = run_price_update(target_date=parsed_date, db=db)
    except ValueError as exc:
        return RedirectResponse(f"/updates?error={str(exc)}", status_code=303)
    message = (
        f"{summary.target_date.isoformat()} attempted={summary.attempted} "
        f"succeeded={summary.succeeded} failed={summary.failed}"
    )
    return RedirectResponse(f"/updates?message={message}", status_code=303)


@router.get("/alerts")
def alerts_page(request: Request):
    return templates.TemplateResponse(request, "alerts.html")
