"""Day 3 tests — Authentication: auth utilities, dependencies, and auth endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient


# ── Auth utility imports ────────────────────────────────────────────

def test_auth_module_imports():
    """auth.py exports all four functions."""
    from app.auth import (
        hash_password, verify_password,
        create_access_token, verify_access_token,
    )
    assert all([hash_password, verify_password, create_access_token, verify_access_token])


# ── Password hashing ───────────────────────────────────────────────

def test_hash_password_returns_bcrypt_hash():
    from app.auth import hash_password

    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_hash_password_different_each_time():
    from app.auth import hash_password

    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2, "Bcrypt should produce different hashes due to salt"


def test_verify_password_correct():
    from app.auth import hash_password, verify_password

    hashed = hash_password("correct")
    assert verify_password("correct", hashed) is True


def test_verify_password_wrong():
    from app.auth import hash_password, verify_password

    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


# ── JWT tokens ──────────────────────────────────────────────────────

def test_create_access_token_returns_string():
    from app.auth import create_access_token

    token = create_access_token(user_id=42)
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_contains_three_parts():
    """JWT has header.payload.signature format."""
    from app.auth import create_access_token

    token = create_access_token(user_id=1)
    parts = token.split(".")
    assert len(parts) == 3


def test_verify_access_token_valid():
    from app.auth import create_access_token, verify_access_token

    token = create_access_token(user_id=7)
    payload = verify_access_token(token)
    assert payload is not None
    assert payload["sub"] == "7"


def test_verify_access_token_contains_exp():
    from app.auth import create_access_token, verify_access_token

    token = create_access_token(user_id=1)
    payload = verify_access_token(token)
    assert "exp" in payload


def test_verify_access_token_invalid():
    from app.auth import verify_access_token

    result = verify_access_token("invalid.token.here")
    assert result is None


def test_verify_access_token_tampered():
    from app.auth import create_access_token, verify_access_token

    token = create_access_token(user_id=1)
    tampered = token[:-5] + "XXXXX"
    result = verify_access_token(tampered)
    assert result is None


# ── Dependencies imports ────────────────────────────────────────────

def test_dependencies_module_imports():
    """dependencies.py exports get_db and get_current_user."""
    from app.dependencies import get_db, get_current_user
    assert all([get_db, get_current_user])


def test_get_db_yields_session():
    """get_db yields a session and closes it."""
    from app.dependencies import get_db

    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        gen.send(None)
    except StopIteration:
        pass


def test_oauth2_scheme_exists():
    """OAuth2PasswordBearer is configured."""
    from app.dependencies import oauth2_scheme
    assert oauth2_scheme is not None


# ── Login schema ────────────────────────────────────────────────────

def test_user_login_schema_exists():
    """UserLogin schema exists with email and password fields."""
    from app.schemas import UserLogin

    login = UserLogin(email="test@example.com", password="secret")
    assert login.email == "test@example.com"
    assert login.password == "secret"


def test_user_login_no_username_field():
    """UserLogin should not have a username field."""
    from app.schemas import UserLogin

    assert "username" not in UserLogin.model_fields


# ── Auth router / endpoints (using TestClient) ─────────────────────

@pytest.fixture()
def app():
    """Create a FastAPI app with auth router and test DB."""
    from fastapi import FastAPI
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.database import Base
    from app.routers.auth import router
    from app.dependencies import get_db
    import app.models  # noqa: F401

    engine = create_engine(settings.DATABASE_URL)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    application = FastAPI()
    application.include_router(router)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db

    yield application, engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(app):
    application, _ = app
    return TestClient(application)


# ── Register endpoint ──────────────────────────────────────────────

def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={
        "username": "user1",
        "email": "dup@example.com",
        "password": "pass",
    })
    resp = client.post("/api/auth/register", json={
        "username": "user2",
        "email": "dup@example.com",
        "password": "pass",
    })
    assert resp.status_code == 409


def test_register_duplicate_username(client):
    client.post("/api/auth/register", json={
        "username": "samename",
        "email": "a@example.com",
        "password": "pass",
    })
    resp = client.post("/api/auth/register", json={
        "username": "samename",
        "email": "b@example.com",
        "password": "pass",
    })
    assert resp.status_code == 409


def test_register_invalid_email(client):
    resp = client.post("/api/auth/register", json={
        "username": "user",
        "email": "not-an-email",
        "password": "pass",
    })
    assert resp.status_code == 422


def test_register_missing_fields(client):
    resp = client.post("/api/auth/register", json={
        "username": "user",
    })
    assert resp.status_code == 422


# ── Login endpoint ──────────────────────────────────────────────────

def test_login_success(client):
    client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "mypassword",
    })
    resp = client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "username": "user3",
        "email": "user3@example.com",
        "password": "rightpass",
    })
    resp = client.post("/api/auth/login", json={
        "email": "user3@example.com",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


def test_login_nonexistent_email(client):
    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert resp.status_code == 401


def test_login_token_is_valid_jwt(client):
    """The token returned by login can be decoded."""
    from app.auth import verify_access_token

    client.post("/api/auth/register", json={
        "username": "jwtuser",
        "email": "jwt@example.com",
        "password": "pass123",
    })
    resp = client.post("/api/auth/login", json={
        "email": "jwt@example.com",
        "password": "pass123",
    })
    token = resp.json()["access_token"]
    payload = verify_access_token(token)
    assert payload is not None
    assert "sub" in payload
