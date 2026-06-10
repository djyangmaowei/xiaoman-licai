from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as app_router
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import alert, ledger, market_data, product, user, valuation  # noqa: F401
from app.services.product_service import seed_products


def bootstrap_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_products(db)


def create_app() -> FastAPI:
    app = FastAPI(title="小满理财")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    bootstrap_database()

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "xiaoman-finance"}

    app.include_router(app_router)

    return app


app = create_app()
