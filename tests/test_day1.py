"""Day 1 tests — config, database connection, and ORM models."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine


# ── Config ───────────────────────────────────────────────────────────

def test_settings_loads():
    """Settings singleton imports and has required fields."""
    from app.config import settings

    assert settings.DATABASE_URL, "DATABASE_URL must not be empty"
    assert settings.JWT_SECRET, "JWT_SECRET must not be empty"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_EXPIRY_MINUTES == 30


# ── Database connection ──────────────────────────────────────────────

async def test_engine_connects():
    """Async engine can reach the PostgreSQL server."""
    from app.database import engine

    assert isinstance(engine, AsyncEngine)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


async def test_session_works():
    """SessionLocal produces a usable async session."""
    from app.database import SessionLocal

    async with SessionLocal() as session:
        result = await session.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        assert db_name, "Should return the current database name"


# ── Models ───────────────────────────────────────────────────────────

def test_models_import():
    """All three ORM models import without errors."""
    from app.models import User, Category, Task

    assert User.__tablename__ == "users"
    assert Category.__tablename__ == "categories"
    assert Task.__tablename__ == "tasks"


def test_user_columns():
    """User model has the expected columns."""
    from app.models import User

    cols = {c.name for c in User.__table__.columns}
    expected = {"id", "email", "username", "hashed_password", "created_at"}
    assert expected == cols


def test_category_columns():
    """Category model has the expected columns."""
    from app.models import Category

    cols = {c.name for c in Category.__table__.columns}
    expected = {"id", "name", "user_id", "created_at"}
    assert expected == cols


def test_task_columns():
    """Task model has the expected columns."""
    from app.models import Task

    cols = {c.name for c in Task.__table__.columns}
    expected = {
        "id", "title", "description", "status", "priority",
        "due_date", "user_id", "category_id", "created_at", "updated_at",
    }
    assert expected == cols


def test_user_relationships():
    """User model has tasks and categories relationships."""
    from app.models import User

    rel_names = {r.key for r in inspect(User).relationships}
    assert "tasks" in rel_names
    assert "categories" in rel_names


def test_task_defaults():
    """Task has correct default values for status and priority."""
    from app.models import Task

    status_col = Task.__table__.columns["status"]
    priority_col = Task.__table__.columns["priority"]
    assert status_col.default.arg == "todo"
    assert priority_col.default.arg == "medium"


# ── Real tables in DB ────────────────────────────────────────────────

@pytest.fixture(autouse=False)
def create_tables():
    """Tables are created once per session by conftest via Alembic migrations."""
    yield


def test_tables_exist_in_db(create_tables, sync_engine):
    """All three tables actually exist in PostgreSQL."""
    with sync_engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        ))
        tables = {row[0] for row in result}

    assert "users" in tables, "users table not found in DB"
    assert "categories" in tables, "categories table not found in DB"
    assert "tasks" in tables, "tasks table not found in DB"


def test_db_columns_match_models(create_tables, sync_engine):
    """Column names in PostgreSQL match the ORM model definitions."""
    from app.models import User, Category, Task

    db_inspector = inspect(sync_engine)

    for model in (User, Category, Task):
        table = model.__tablename__
        db_cols = {c["name"] for c in db_inspector.get_columns(table)}
        model_cols = {c.name for c in model.__table__.columns}
        assert db_cols == model_cols, (
            f"Column mismatch in '{table}': "
            f"db={db_cols}, model={model_cols}"
        )
