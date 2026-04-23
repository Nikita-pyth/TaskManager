"""Test fixtures.

Creates a dedicated `taskmanager_test` database once per test session,
runs Alembic migrations against it, then drops it at the end. Tests hit
this DB — the dev `taskmanager` DB is left alone.

`DATABASE_URL` is overridden at module top before any `app.*` import so
that `app.config.settings`, `app.database.engine`, and Alembic's env.py
all resolve to the test DB.
"""

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def _read_env_var(name: str) -> str | None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return None
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


_TEST_DB_NAME = "taskmanager_test"

_source_url = os.environ.get("DATABASE_URL") or _read_env_var("DATABASE_URL")
if not _source_url:
    raise RuntimeError("DATABASE_URL is not set; cannot configure test DB")

_parsed = urlparse(_source_url)
_ADMIN_URL = urlunparse(_parsed._replace(path="/postgres"))
_TEST_URL = urlunparse(_parsed._replace(path=f"/{_TEST_DB_NAME}"))

os.environ["DATABASE_URL"] = _TEST_URL


import pytest
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient


def _admin_exec(sql: str) -> None:
    engine = create_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
    finally:
        engine.dispose()


def _truncate_all() -> None:
    from app.database import engine
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE tasks, categories, users RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    _admin_exec(f"DROP DATABASE IF EXISTS {_TEST_DB_NAME} WITH (FORCE)")
    _admin_exec(f"CREATE DATABASE {_TEST_DB_NAME}")

    from alembic import command
    from alembic.config import Config

    project_root = Path(__file__).resolve().parent.parent
    cfg = Config(str(project_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(project_root / "alembic"))
    command.upgrade(cfg, "head")

    yield

    try:
        from app.database import engine
        engine.dispose()
    except Exception:
        pass
    _admin_exec(f"DROP DATABASE IF EXISTS {_TEST_DB_NAME} WITH (FORCE)")


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def clean_tables():
    _truncate_all()
    yield


@pytest.fixture(scope="module")
def clean_tables_module():
    _truncate_all()
    yield
