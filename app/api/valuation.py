from fastapi import APIRouter

router = APIRouter(prefix="/api/valuation", tags=["valuation"])


@router.get("/status")
def valuation_status() -> dict[str, str]:
    return {"status": "ready"}
