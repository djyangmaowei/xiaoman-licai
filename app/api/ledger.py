from fastapi import APIRouter

router = APIRouter(prefix="/api/ledger", tags=["ledger"])


@router.get("/status")
def ledger_status() -> dict[str, str]:
    return {"status": "ready"}
