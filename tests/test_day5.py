"""Day 5 tests — HTML Templates & Page Routes."""

# `client` is provided by tests/conftest.py.


# ── Page routes ─────────────────────────────────────────────────────

def test_index_redirects_to_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert "/login" in resp.headers["location"]


def test_login_page_renders(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Login" in resp.text


def test_login_page_has_form(client):
    resp = client.get("/login")
    assert 'id="login-form"' in resp.text
    assert 'name="email"' in resp.text
    assert 'name="password"' in resp.text


def test_register_page_renders(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert "Register" in resp.text


def test_register_page_has_form(client):
    resp = client.get("/register")
    assert 'id="register-form"' in resp.text
    assert 'name="username"' in resp.text
    assert 'name="email"' in resp.text
    assert 'name="password"' in resp.text


def test_dashboard_page_renders(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "Dashboard" in resp.text


def test_dashboard_has_category_sidebar(client):
    resp = client.get("/dashboard")
    assert 'id="category-list"' in resp.text
    assert 'id="add-category-form"' in resp.text


def test_dashboard_has_task_section(client):
    resp = client.get("/dashboard")
    assert 'id="task-list"' in resp.text
    assert 'id="task-form"' in resp.text


def test_dashboard_has_filters(client):
    resp = client.get("/dashboard")
    assert 'id="filter-status"' in resp.text
    assert 'id="filter-priority"' in resp.text
    assert 'id="filter-search"' in resp.text
    assert 'id="sort-by"' in resp.text


# ── Static files ────────────────────────────────────────────────────

def test_css_served(client):
    resp = client.get("/static/css/style.css")
    assert resp.status_code == 200
    assert "text/css" in resp.headers["content-type"]


def test_js_served(client):
    resp = client.get("/static/js/app.js")
    assert resp.status_code == 200
    assert "javascript" in resp.headers["content-type"]


# ── Templates extend base ──────────────────────────────────────────

def test_login_includes_navbar(client):
    resp = client.get("/login")
    assert 'class="navbar' in resp.text
    assert 'Task Manager' in resp.text


def test_login_includes_css(client):
    resp = client.get("/login")
    assert "/static/css/style.css" in resp.text


def test_login_includes_js(client):
    resp = client.get("/login")
    assert "/static/js/app.js" in resp.text


def test_pages_link_to_each_other(client):
    login_resp = client.get("/login")
    assert '/register' in login_resp.text

    register_resp = client.get("/register")
    assert '/login' in register_resp.text
