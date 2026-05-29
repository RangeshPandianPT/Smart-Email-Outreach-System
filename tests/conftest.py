import pytest

from src.core import database


@pytest.fixture(autouse=True)
def mock_rate_limiter_sleep(monkeypatch):
    """Disable time.sleep in the rate limiter for faster tests."""
    try:
        from src.services import rate_limiter
        monkeypatch.setattr(rate_limiter.time, "sleep", lambda x: None)
    except ImportError:
        pass

@pytest.fixture(autouse=True)
def isolated_database(monkeypatch, tmp_path):
    """Use a fresh SQLite file for every test."""
    test_db = tmp_path / "crm_test.db"
    monkeypatch.setattr(database, "DB_FILE", str(test_db))
    database.init_db()
    yield
