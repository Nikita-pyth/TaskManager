# Task Manager — 7-Day Implementation Roadmap

> Each day represents roughly equal developer effort (~1-1.5 hours).
> The project skeleton (empty files, folder structure, requirements.txt, venv, .gitignore) is already in place.

---

## Day 1 — Foundation

**Goal:** Establish the project config, database connection, and ORM models.

**Files:**
- `.env` — create with DB URL, JWT secret, algorithm, token expiry
- `app/config.py` — `Settings` class via pydantic-settings, reads `.env`
- `app/database.py` — SQLAlchemy engine, `SessionLocal`, declarative `Base`
- `app/models.py` — ORM models: `User`, `Category`, `Task` with relationships and cascade deletes

**Done when:** Python imports of `config`, `database`, and `models` work without errors; models reflect the 3-table schema from the plan.

---

## Day 2 — Migrations & Schemas

**Goal:** Initialize Alembic, generate the first migration, and define all Pydantic schemas.

**Files:**
- `alembic.ini` — configure DB URL (or read from `.env`)
- `alembic/env.py` — import `Base` metadata, configure target_metadata
- `alembic/versions/` — auto-generate first migration (3 tables)
- `app/schemas.py` — all request/response Pydantic models:
  - `UserCreate`, `UserOut`, `Token`
  - `CategoryCreate`, `CategoryOut`
  - `TaskCreate`, `TaskUpdate`, `TaskOut`

**Done when:** `alembic upgrade head` creates all 3 tables in PostgreSQL; schemas import cleanly and validate sample data.

---

## Day 3 — Authentication

**Goal:** Implement password hashing, JWT token utilities, and the auth API endpoints.

**Files:**
- `app/auth.py` — `hash_password()`, `verify_password()` (bcrypt via passlib), `create_access_token()`, `verify_access_token()` (python-jose, HS256)
- `app/dependencies.py` — `get_db()` session generator, `get_current_user()` dependency (decodes JWT, fetches user)
- `app/routers/auth.py` — `POST /api/auth/register`, `POST /api/auth/login`

**Done when:** Register and login work via Swagger UI (`/docs`); login returns a valid JWT; invalid credentials return 401/403.

---

## Day 4 — Categories & Tasks API

**Goal:** Build the full CRUD API for categories and tasks, including filtering and sorting.

**Files:**
- `app/routers/categories.py` — `GET /api/categories`, `POST /api/categories`, `DELETE /api/categories/{id}` (all scoped to current user)
- `app/routers/tasks.py` — `GET /api/tasks` (with query params: `status`, `priority`, `category_id`, `search`, `sort_by`, `order`), `POST /api/tasks`, `GET /api/tasks/{id}`, `PUT /api/tasks/{id}`, `DELETE /api/tasks/{id}`
- `app/main.py` — wire up all routers, mount static/templates (minimal wiring to enable Swagger testing)

**Done when:** All 8 endpoints respond correctly in Swagger with a valid JWT; filters and sorting on `GET /api/tasks` work; users can only access their own data.

---

## Day 5 — HTML Templates & Page Routes

**Goal:** Create the Jinja2 templates and the page-serving router so the app has a navigable frontend shell.

**Files:**
- `app/routers/pages.py` — `GET /` (redirect), `GET /login`, `GET /register`, `GET /dashboard`
- `app/templates/base.html` — shared HTML skeleton (head, nav bar, content block, script includes)
- `app/templates/login.html` — login form (email + password)
- `app/templates/register.html` — registration form (username + email + password)
- `app/templates/dashboard.html` — main task board layout: category sidebar, task list area, filter controls, create-task form/modal

**Done when:** All four pages render in the browser with proper layout; navigation between pages works; dashboard shows placeholder structure for tasks and categories.

---

## Day 6 — Frontend Logic (JavaScript)

**Goal:** Make the frontend fully interactive — auth flow, task CRUD, category management, filtering.

**Files:**
- `app/static/js/app.js` — all client-side logic:
  - Auth: register form submit, login form submit, store JWT in localStorage, redirect on success, logout (clear token)
  - API helper: `fetchAPI()` wrapper that attaches `Authorization: Bearer` header
  - Dashboard: load and render categories, load and render tasks, create/edit/delete tasks, create/delete categories
  - Filters: apply status/priority/category filters, search, sort
  - UX: show/hide forms or modals, display validation errors, redirect to `/login` on 401

**Done when:** A user can register, log in, create categories, create/edit/delete tasks, filter and sort tasks, and log out — all through the browser UI.

---

## Day 7 — Styling & Polish

**Goal:** Style the app, handle edge cases, and finalize everything for submission.

**Files:**
- `app/static/css/style.css` — full styling (~200 lines): layout, forms, buttons, task cards, status/priority badges, responsive basics, nav bar, modals
- `app/main.py` — final review: CORS (if needed), exception handlers, startup event
- General polish:
  - Consistent error messages from API (HTTPException details)
  - Empty-state messages in UI (no tasks yet, no categories yet)
  - Form validation feedback
  - Token expiry handling (redirect to login)
  - Final `.gitignore` review
  - Quick smoke test of the full flow: register -> login -> create category -> create task -> filter -> edit -> delete -> logout

**Done when:** The app looks clean, all features work end-to-end, no unhandled errors, and the project is ready to demo/submit.
