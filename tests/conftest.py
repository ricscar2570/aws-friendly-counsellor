import os

import pytest

from aws_friendly_counsellor.infrastructure.persistence import reset_store

os.environ.setdefault("APP_ENVIRONMENT", "test")
os.environ.setdefault("ALLOW_LOCAL_IDENTITY", "true")
os.environ.setdefault("LOCAL_IDENTITY_SUBJECT", "00000000-0000-4000-8000-000000000001")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "1000")
os.environ.setdefault("RATE_LIMIT_WINDOW", "60")
os.environ.setdefault("STORAGE_BACKEND", "sqlite")


@pytest.fixture(autouse=True)
def isolated_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "awsfc-test.db"))
    reset_store()
    yield
    reset_store()
