from app.core.security import can_write


def ensure_write_allowed(role: str) -> None:
    if not can_write(role):
        raise PermissionError("viewer role cannot modify xiaoman finance data")
