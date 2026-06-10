from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="小满理财")

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "xiaoman-finance"}

    return app


app = create_app()
