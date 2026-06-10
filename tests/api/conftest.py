import pytest


@pytest.fixture
def sample_database_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"
