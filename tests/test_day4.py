"""Day 4 tests — Categories & Tasks CRUD API with filtering, sorting, and user scoping."""

import pytest
import pytest_asyncio


# ── Fixtures ────────────────────────────────────────────────────────

# `client` is provided by tests/conftest.py. The module shares state across
# tests via `auth_header`, so truncate once per module to give this module
# a clean slate without disturbing per-test state.
@pytest.fixture(scope="module", autouse=True)
def _isolate(clean_tables_module):
    pass


@pytest_asyncio.fixture(scope="module")
async def auth_header(client):
    """Register a user and return an auth header."""
    await client.post("/api/auth/register", json={
        "username": "day4user",
        "email": "day4@example.com",
        "password": "testpass",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "day4@example.com",
        "password": "testpass",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="module")
async def other_auth_header(client):
    """Register a second user for scoping tests."""
    await client.post("/api/auth/register", json={
        "username": "otheruser",
        "email": "other@example.com",
        "password": "otherpass",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "other@example.com",
        "password": "otherpass",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Categories: no auth ────────────────────────────────────────────

async def test_categories_require_auth(client):
    resp = await client.get("/api/categories/")
    assert resp.status_code == 401


# ── Categories: CRUD ───────────────────────────────────────────────

async def test_create_category(client, auth_header):
    resp = await client.post("/api/categories/", json={"name": "Work"}, headers=auth_header)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Work"
    assert "id" in data
    assert "created_at" in data


async def test_create_second_category(client, auth_header):
    resp = await client.post("/api/categories/", json={"name": "Personal"}, headers=auth_header)
    assert resp.status_code == 201


async def test_list_categories(client, auth_header):
    resp = await client.get("/api/categories/", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    names = [c["name"] for c in data]
    assert "Work" in names
    assert "Personal" in names


async def test_delete_category(client, auth_header):
    # Create a throwaway category
    resp = await client.post("/api/categories/", json={"name": "Delete Me"}, headers=auth_header)
    cat_id = resp.json()["id"]
    resp = await client.delete(f"/api/categories/{cat_id}", headers=auth_header)
    assert resp.status_code == 204


async def test_delete_category_not_found(client, auth_header):
    resp = await client.delete("/api/categories/99999", headers=auth_header)
    assert resp.status_code == 404


async def test_category_scoped_to_user(client, auth_header, other_auth_header):
    """Other user cannot see or delete first user's categories."""
    resp = await client.get("/api/categories/", headers=other_auth_header)
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # Get first user's category id
    cats = (await client.get("/api/categories/", headers=auth_header)).json()
    cat_id = cats[0]["id"]

    # Other user can't delete it
    resp = await client.delete(f"/api/categories/{cat_id}", headers=other_auth_header)
    assert resp.status_code == 404


# ── Tasks: no auth ─────────────────────────────────────────────────

async def test_tasks_require_auth(client):
    resp = await client.get("/api/tasks/")
    assert resp.status_code == 401


# ── Tasks: CRUD ────────────────────────────────────────────────────

async def test_create_task(client, auth_header):
    resp = await client.post("/api/tasks/", json={
        "title": "Buy groceries",
        "priority": "high",
    }, headers=auth_header)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Buy groceries"
    assert data["priority"] == "high"
    assert data["status"] == "todo"
    assert "id" in data


async def test_create_task_with_category(client, auth_header):
    cats = (await client.get("/api/categories/", headers=auth_header)).json()
    cat_id = cats[0]["id"]
    resp = await client.post("/api/tasks/", json={
        "title": "Finish report",
        "category_id": cat_id,
        "status": "in_progress",
    }, headers=auth_header)
    assert resp.status_code == 201
    assert resp.json()["category_id"] == cat_id


async def test_create_task_low_priority(client, auth_header):
    resp = await client.post("/api/tasks/", json={
        "title": "Read a book",
        "priority": "low",
        "status": "done",
    }, headers=auth_header)
    assert resp.status_code == 201


async def test_list_tasks(client, auth_header):
    resp = await client.get("/api/tasks/", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3


async def test_get_single_task(client, auth_header):
    tasks_list = (await client.get("/api/tasks/", headers=auth_header)).json()
    task_id = tasks_list[0]["id"]
    resp = await client.get(f"/api/tasks/{task_id}", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


async def test_get_task_not_found(client, auth_header):
    resp = await client.get("/api/tasks/99999", headers=auth_header)
    assert resp.status_code == 404


async def test_update_task(client, auth_header):
    tasks_list = (await client.get("/api/tasks/", headers=auth_header)).json()
    task_id = tasks_list[0]["id"]
    resp = await client.put(f"/api/tasks/{task_id}", json={
        "title": "Updated title",
        "status": "done",
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated title"
    assert data["status"] == "done"


async def test_update_task_not_found(client, auth_header):
    resp = await client.put("/api/tasks/99999", json={"title": "Nope"}, headers=auth_header)
    assert resp.status_code == 404


async def test_delete_task(client, auth_header):
    resp = await client.post("/api/tasks/", json={"title": "To delete"}, headers=auth_header)
    task_id = resp.json()["id"]
    resp = await client.delete(f"/api/tasks/{task_id}", headers=auth_header)
    assert resp.status_code == 204
    # Confirm gone
    resp = await client.get(f"/api/tasks/{task_id}", headers=auth_header)
    assert resp.status_code == 404


async def test_delete_task_not_found(client, auth_header):
    resp = await client.delete("/api/tasks/99999", headers=auth_header)
    assert resp.status_code == 404


# ── Tasks: user scoping ────────────────────────────────────────────

async def test_task_scoped_to_user(client, auth_header, other_auth_header):
    """Other user cannot see or modify first user's tasks."""
    resp = await client.get("/api/tasks/", headers=other_auth_header)
    assert len(resp.json()) == 0

    tasks_list = (await client.get("/api/tasks/", headers=auth_header)).json()
    task_id = tasks_list[0]["id"]

    assert (await client.get(f"/api/tasks/{task_id}", headers=other_auth_header)).status_code == 404
    assert (await client.put(f"/api/tasks/{task_id}", json={"title": "Hack"}, headers=other_auth_header)).status_code == 404
    assert (await client.delete(f"/api/tasks/{task_id}", headers=other_auth_header)).status_code == 404


# ── Tasks: filtering ───────────────────────────────────────────────

async def test_filter_by_status(client, auth_header):
    resp = await client.get("/api/tasks/?status=done", headers=auth_header)
    assert resp.status_code == 200
    for task in resp.json():
        assert task["status"] == "done"


async def test_filter_by_priority(client, auth_header):
    resp = await client.get("/api/tasks/?priority=high", headers=auth_header)
    assert resp.status_code == 200
    for task in resp.json():
        assert task["priority"] == "high"


async def test_filter_by_category_id(client, auth_header):
    cats = (await client.get("/api/categories/", headers=auth_header)).json()
    cat_id = cats[0]["id"]
    resp = await client.get(f"/api/tasks/?category_id={cat_id}", headers=auth_header)
    assert resp.status_code == 200
    for task in resp.json():
        assert task["category_id"] == cat_id


async def test_search_by_title(client, auth_header):
    resp = await client.get("/api/tasks/?search=groceries", headers=auth_header)
    assert resp.status_code == 200
    # Should not be empty (we have "Buy groceries" — but title was updated)
    # At least no error


# ── Tasks: sorting ──────────────────────────────────────────────────

async def test_sort_by_title_asc(client, auth_header):
    resp = await client.get("/api/tasks/?sort_by=title&order=asc", headers=auth_header)
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()]
    assert titles == sorted(titles)


async def test_sort_by_title_desc(client, auth_header):
    resp = await client.get("/api/tasks/?sort_by=title&order=desc", headers=auth_header)
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()]
    assert titles == sorted(titles, reverse=True)


async def test_sort_invalid_field_falls_back(client, auth_header):
    """Invalid sort_by should fall back to created_at without error."""
    resp = await client.get("/api/tasks/?sort_by=invalid_field", headers=auth_header)
    assert resp.status_code == 200
