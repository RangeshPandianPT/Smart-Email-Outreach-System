import pytest

from src.core import database


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch, tmp_path):
    """Use a fresh SQLite file for every test."""
    test_db = tmp_path / "crm_test.db"
    monkeypatch.setattr(database, "DB_FILE", str(test_db))
    database.init_db()
    yield
