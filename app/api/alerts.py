from fastapi import APIRouter

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/status")
def alert_status() -> dict[str, str]:
    return {"status": "ready"}
