from fastapi import FastAPI

from app.api.routes import router as app_router


def create_app() -> FastAPI:
    app = FastAPI(title="小满理财")

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "xiaoman-finance"}

    app.include_router(app_router)

    return app


app = create_app()
