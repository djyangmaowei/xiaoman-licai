from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_local_database_file():
    from app.db.session import engine

    db_path = Path("xiaoman-dev.db")
    engine.dispose()
    db_path.unlink(missing_ok=True)
    yield
    engine.dispose()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def sample_database_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"
