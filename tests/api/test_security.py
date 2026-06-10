from app.core.security import can_write


def test_admin_can_write():
    assert can_write("admin") is True


def test_viewer_cannot_write():
    assert can_write("viewer") is False
