"""Day 2 tests — Alembic migrations and Pydantic schemas."""

import pytest
from datetime import datetime, date, timedelta, timezone
from pydantic import ValidationError
from sqlalchemy import inspect, text


# ── Alembic config ──────────────────────────────────────────────────

def test_alembic_ini_has_no_hardcoded_url():
    """alembic.ini should NOT contain a hardcoded sqlalchemy.url value."""
    from pathlib import Path

    ini_text = Path("alembic.ini").read_text()
    for line in ini_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("sqlalchemy.url"):
            # The line should not exist at all in the ini
            pytest.fail("alembic.ini contains a hardcoded sqlalchemy.url")


def test_alembic_env_sets_target_metadata():
    """env.py should set target_metadata to Base.metadata."""
    from pathlib import Path

    env_text = Path("alembic/env.py").read_text()
    assert "target_metadata = Base.metadata" in env_text
    assert "from app.database import Base" in env_text
    assert "import app.models" in env_text


# ── Migration applied correctly ─────────────────────────────────────

def test_alembic_version_table_exists(sync_engine):
    """alembic_version table exists, proving migrations have been applied."""
    with sync_engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'alembic_version'"
        ))
        assert result.fetchone() is not None, "alembic_version table missing"


def test_alembic_current_revision_is_set(sync_engine):
    """A migration revision has been recorded in alembic_version."""
    with sync_engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        assert row is not None, "No revision found — migration not applied"
        assert len(row[0]) > 0, "Revision string is empty"


def test_migration_created_all_tables(sync_engine):
    """The migration created users, categories, and tasks tables."""
    db_inspector = inspect(sync_engine)
    tables = set(db_inspector.get_table_names())

    assert "users" in tables
    assert "categories" in tables
    assert "tasks" in tables


def test_migration_users_columns(sync_engine):
    """users table has correct columns after migration."""
    db_inspector = inspect(sync_engine)
    cols = {c["name"] for c in db_inspector.get_columns("users")}
    expected = {"id", "email", "username", "hashed_password", "created_at"}
    assert cols == expected


def test_migration_categories_columns(sync_engine):
    """categories table has correct columns after migration."""
    db_inspector = inspect(sync_engine)
    cols = {c["name"] for c in db_inspector.get_columns("categories")}
    expected = {"id", "name", "user_id", "created_at"}
    assert cols == expected


def test_migration_tasks_columns(sync_engine):
    """tasks table has correct columns after migration."""
    db_inspector = inspect(sync_engine)
    cols = {c["name"] for c in db_inspector.get_columns("tasks")}
    expected = {
        "id", "title", "description", "status", "priority",
        "due_date", "user_id", "category_id", "created_at", "updated_at",
    }
    assert cols == expected


def test_migration_users_email_index(sync_engine):
    """users.email has a unique index after migration."""
    db_inspector = inspect(sync_engine)
    indexes = db_inspector.get_indexes("users")
    email_indexes = [i for i in indexes if "email" in i["column_names"]]
    assert len(email_indexes) > 0, "No index on users.email"
    assert email_indexes[0]["unique"] is True


def test_migration_foreign_keys_categories(sync_engine):
    """categories.user_id references users.id."""
    db_inspector = inspect(sync_engine)
    fks = db_inspector.get_foreign_keys("categories")
    user_fks = [fk for fk in fks if fk["referred_table"] == "users"]
    assert len(user_fks) == 1
    assert user_fks[0]["constrained_columns"] == ["user_id"]
    assert user_fks[0]["referred_columns"] == ["id"]


def test_migration_foreign_keys_tasks(sync_engine):
    """tasks has foreign keys to users.id and categories.id."""
    db_inspector = inspect(sync_engine)
    fks = db_inspector.get_foreign_keys("tasks")
    referred = {fk["referred_table"]: fk for fk in fks}

    assert "users" in referred
    assert referred["users"]["constrained_columns"] == ["user_id"]

    assert "categories" in referred
    assert referred["categories"]["constrained_columns"] == ["category_id"]


# ── Schema imports ──────────────────────────────────────────────────

def test_all_schemas_import():
    """All 8 schema classes import without errors."""
    from app.schemas import (
        UserCreate, UserOut, Token,
        CategoryCreate, CategoryOut,
        TaskCreate, TaskUpdate, TaskOut,
    )
    assert all([
        UserCreate, UserOut, Token,
        CategoryCreate, CategoryOut,
        TaskCreate, TaskUpdate, TaskOut,
    ])


# ── UserCreate ──────────────────────────────────────────────────────

def test_user_create_valid():
    from app.schemas import UserCreate

    u = UserCreate(username="alice", email="alice@example.com", password="secret123")
    assert u.username == "alice"
    assert u.email == "alice@example.com"
    assert u.password == "secret123"


def test_user_create_invalid_email():
    from app.schemas import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(username="alice", email="not-an-email", password="secret123")


def test_user_create_missing_fields():
    from app.schemas import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(username="alice")  # missing email and password


# ── UserOut ─────────────────────────────────────────────────────────

def test_user_out_valid():
    from app.schemas import UserOut

    u = UserOut(
        id=1, username="alice", email="alice@example.com",
        created_at=datetime.now(timezone.utc),
    )
    assert u.id == 1
    assert u.username == "alice"


def test_user_out_no_password_field():
    """UserOut should not expose a password field."""
    from app.schemas import UserOut

    fields = set(UserOut.model_fields.keys())
    assert "password" not in fields
    assert "hashed_password" not in fields


def test_user_out_from_attributes():
    """UserOut has from_attributes=True for ORM compatibility."""
    from app.schemas import UserOut

    assert UserOut.model_config.get("from_attributes") is True


# ── Token ───────────────────────────────────────────────────────────

def test_token_valid():
    from app.schemas import Token

    t = Token(access_token="abc.def.ghi")
    assert t.access_token == "abc.def.ghi"
    assert t.token_type == "bearer"


def test_token_custom_type():
    from app.schemas import Token

    t = Token(access_token="abc", token_type="custom")
    assert t.token_type == "custom"


# ── CategoryCreate ──────────────────────────────────────────────────

def test_category_create_valid():
    from app.schemas import CategoryCreate

    c = CategoryCreate(name="Work")
    assert c.name == "Work"


def test_category_create_missing_name():
    from app.schemas import CategoryCreate

    with pytest.raises(ValidationError):
        CategoryCreate()


# ── CategoryOut ─────────────────────────────────────────────────────

def test_category_out_valid():
    from app.schemas import CategoryOut

    c = CategoryOut(id=1, name="Work", created_at=datetime.now(timezone.utc))
    assert c.id == 1
    assert c.name == "Work"


def test_category_out_from_attributes():
    from app.schemas import CategoryOut

    assert CategoryOut.model_config.get("from_attributes") is True


# ── TaskCreate ──────────────────────────────────────────────────────

def test_task_create_minimal():
    """TaskCreate only requires title; everything else has defaults."""
    from app.schemas import TaskCreate

    t = TaskCreate(title="Buy milk")
    assert t.title == "Buy milk"
    assert t.status == "todo"
    assert t.priority == "medium"
    assert t.description is None
    assert t.due_date is None
    assert t.category_id is None


def test_task_create_full():
    from app.schemas import TaskCreate

    future = date.today() + timedelta(days=30)
    t = TaskCreate(
        title="Deploy app",
        description="Push to production",
        status="in_progress",
        priority="high",
        due_date=future,
        category_id=5,
    )
    assert t.title == "Deploy app"
    assert t.due_date == future
    assert t.category_id == 5


def test_task_create_missing_title():
    from app.schemas import TaskCreate

    with pytest.raises(ValidationError):
        TaskCreate()


# ── TaskUpdate ──────────────────────────────────────────────────────

def test_task_update_all_optional():
    """TaskUpdate should accept no fields (empty update)."""
    from app.schemas import TaskUpdate

    t = TaskUpdate()
    assert t.title is None
    assert t.status is None
    assert t.priority is None


def test_task_update_partial():
    from app.schemas import TaskUpdate

    t = TaskUpdate(status="done", priority="low")
    assert t.status == "done"
    assert t.priority == "low"
    assert t.title is None  # untouched fields stay None


# ── TaskOut ─────────────────────────────────────────────────────────

def test_task_out_valid():
    from app.schemas import TaskOut

    now = datetime.now(timezone.utc)
    t = TaskOut(
        id=1, title="Test", description=None,
        status="todo", priority="medium",
        due_date=None, category_id=None,
        created_at=now, updated_at=now,
    )
    assert t.id == 1
    assert t.title == "Test"


def test_task_out_from_attributes():
    from app.schemas import TaskOut

    assert TaskOut.model_config.get("from_attributes") is True


def test_task_out_has_timestamps():
    """TaskOut must include both created_at and updated_at."""
    from app.schemas import TaskOut

    fields = set(TaskOut.model_fields.keys())
    assert "created_at" in fields
    assert "updated_at" in fields
