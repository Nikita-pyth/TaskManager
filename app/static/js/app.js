// ── API helper ──────────────────────────────────────────────────

async function fetchAPI(url, options = {}) {
    const token = localStorage.getItem("token");
    const headers = { "Content-Type": "application/json", ...options.headers };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const skipAuthRedirect = options.skipAuthRedirect;
    delete options.skipAuthRedirect;

    const resp = await fetch(url, { ...options, headers });

    if (resp.status === 401 && !skipAuthRedirect) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        return null;
    }
    return resp;
}

function showError(msg) {
    const el = document.getElementById("error-msg");
    if (el) { el.textContent = msg; el.style.display = "block"; el.className = "alert alert-danger"; }
}

function hideError() {
    const el = document.getElementById("error-msg");
    if (el) el.style.display = "none";
}

// ── Nav toggle ──────────────────────────────────────────────────

function updateNav() {
    const token = localStorage.getItem("token");
    const navLinks = document.getElementById("nav-links");
    const navAuth = document.getElementById("nav-auth");
    const usernameEl = document.getElementById("nav-username");
    if (token) {
        if (navLinks) navLinks.style.display = "none";
        if (navAuth) { navAuth.style.display = "flex"; navAuth.classList.add("align-items-center"); }
        if (usernameEl) usernameEl.textContent = localStorage.getItem("username") || "";
    } else {
        if (navLinks) navLinks.style.display = "flex";
        if (navAuth) navAuth.style.display = "none";
    }
}

// ── Auth: Register ──────────────────────────────────────────────

function initRegister() {
    const form = document.getElementById("register-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError();
        const body = {
            username: document.getElementById("username").value,
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
        };
        const resp = await fetchAPI("/api/auth/register", {
            method: "POST",
            body: JSON.stringify(body),
            skipAuthRedirect: true,
        });
        if (!resp) return;
        if (resp.ok) {
            window.location.href = "/login";
        } else {
            const data = await resp.json();
            showError(data.detail || "Registration failed");
        }
    });
}

// ── Auth: Login ─────────────────────────────────────────────────

function initLogin() {
    const form = document.getElementById("login-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError();
        const body = {
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
        };
        const resp = await fetchAPI("/api/auth/login", {
            method: "POST",
            body: JSON.stringify(body),
            skipAuthRedirect: true,
        });
        if (!resp) return;
        if (resp.ok) {
            const data = await resp.json();
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("username", data.username);
            window.location.href = "/dashboard";
        } else {
            const data = await resp.json();
            showError(data.detail || "Login failed");
        }
    });
}

// ── Logout ──────────────────────────────────────────────────────

function initLogout() {
    const btn = document.getElementById("logout-btn");
    if (!btn) return;
    btn.addEventListener("click", () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        window.location.href = "/login";
    });
}

// ── Dashboard ───────────────────────────────────────────────────

let allCategories = [];

async function loadCategories() {
    const resp = await fetchAPI("/api/categories/");
    if (!resp || !resp.ok) return;
    allCategories = await resp.json();
    renderCategoryList();
    populateCategoryDropdowns();
}

function renderCategoryList() {
    const ul = document.getElementById("category-list");
    const noMsg = document.getElementById("no-categories-msg");
    if (!ul) return;

    if (allCategories.length === 0) {
        ul.innerHTML = "";
        if (noMsg) noMsg.style.display = "block";
        return;
    }
    if (noMsg) noMsg.style.display = "none";

    ul.innerHTML = allCategories.map(c => `
        <li class="list-group-item">
            <span>${c.name}</span>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${c.id})">&times;</button>
        </li>
    `).join("");
}

function populateCategoryDropdowns() {
    const filterCat = document.getElementById("filter-category");
    const taskCat = document.getElementById("task-category");

    const options = '<option value="">None</option>' +
        allCategories.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    const filterOptions = '<option value="">All categories</option>' +
        allCategories.map(c => `<option value="${c.id}">${c.name}</option>`).join("");

    if (taskCat) taskCat.innerHTML = options;
    if (filterCat) filterCat.innerHTML = filterOptions;
}

function initAddCategory() {
    const form = document.getElementById("add-category-form");
    if (!form) return;
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = document.getElementById("new-category-name");
        const name = input.value.trim();
        if (!name) return;
        const resp = await fetchAPI("/api/categories/", {
            method: "POST",
            body: JSON.stringify({ name }),
        });
        if (resp && resp.ok) {
            input.value = "";
            await loadCategories();
        }
    });
}

async function deleteCategory(id) {
    if (!confirm("Are you sure you want to delete this category?")) return;
    const resp = await fetchAPI(`/api/categories/${id}`, { method: "DELETE" });
    if (resp && (resp.ok || resp.status === 204)) {
        await loadCategories();
        await loadTasks();
    }
}

// ── Tasks ───────────────────────────────────────────────────────

async function loadTasks() {
    const params = new URLSearchParams();
    const status = document.getElementById("filter-status")?.value;
    const priority = document.getElementById("filter-priority")?.value;
    const categoryId = document.getElementById("filter-category")?.value;
    const search = document.getElementById("filter-search")?.value;
    const sortBy = document.getElementById("sort-by")?.value;
    const sortOrder = document.getElementById("sort-order")?.value;

    if (status) params.set("status", status);
    if (priority) params.set("priority", priority);
    if (categoryId) params.set("category_id", categoryId);
    if (search) params.set("search", search);
    if (sortBy) params.set("sort_by", sortBy);
    if (sortOrder) params.set("order", sortOrder);

    const resp = await fetchAPI(`/api/tasks/?${params}`);
    if (!resp || !resp.ok) return;
    const tasks = await resp.json();
    renderTasks(tasks);
}

function getCategoryName(id) {
    const cat = allCategories.find(c => c.id === id);
    return cat ? cat.name : "";
}

function renderTasks(tasks) {
    const list = document.getElementById("task-list");
    const noMsg = document.getElementById("no-tasks-msg");
    if (!list) return;

    if (tasks.length === 0) {
        list.innerHTML = "";
        if (noMsg) noMsg.style.display = "block";
        return;
    }
    if (noMsg) noMsg.style.display = "none";

    list.innerHTML = tasks.map(t => `
        <div class="card shadow-sm mb-2" data-task-id="${t.id}">
            <div class="card-body py-2 task-card">
                <div class="task-card-body">
                    <h6 class="mb-1">${t.title}</h6>
                    ${t.description ? `<p class="text-muted small mb-1">${t.description}</p>` : ""}
                    <div class="d-flex flex-wrap gap-1">
                        <span class="badge badge-${t.status}">${t.status.replace("_", " ")}</span>
                        <span class="badge badge-${t.priority}">${t.priority}</span>
                        ${t.category_id ? `<span class="badge bg-secondary">${getCategoryName(t.category_id)}</span>` : ""}
                        ${t.due_date ? `<span class="badge bg-info text-dark">Due: ${t.due_date}</span>` : ""}
                    </div>
                </div>
                <div class="task-card-actions d-flex gap-1">
                    <button class="btn btn-sm btn-outline-primary" onclick="editTask(${t.id})">Edit</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteTask(${t.id})">Del</button>
                </div>
            </div>
        </div>
    `).join("");
}

// ── Task form ───────────────────────────────────────────────────

function initTaskForm() {
    const showBtn = document.getElementById("show-add-task");
    const wrapper = document.getElementById("task-form-wrapper");
    const cancelBtn = document.getElementById("cancel-task");
    const form = document.getElementById("task-form");

    if (!form) return;

    showBtn?.addEventListener("click", () => {
        resetTaskForm();
        showBtn.after(wrapper);
        wrapper.style.display = "block";
        showBtn.style.display = "none";
    });

    cancelBtn?.addEventListener("click", () => {
        wrapper.style.display = "none";
        showBtn.style.display = "inline-block";
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const taskId = document.getElementById("task-id").value;
        const body = {
            title: document.getElementById("task-title").value,
            description: document.getElementById("task-description").value || null,
            status: document.getElementById("task-status").value,
            priority: document.getElementById("task-priority").value,
            due_date: document.getElementById("task-due-date").value || null,
            category_id: document.getElementById("task-category").value || null,
        };
        if (body.category_id) body.category_id = parseInt(body.category_id);

        let resp;
        if (taskId) {
            resp = await fetchAPI(`/api/tasks/${taskId}`, {
                method: "PUT",
                body: JSON.stringify(body),
            });
        } else {
            resp = await fetchAPI("/api/tasks/", {
                method: "POST",
                body: JSON.stringify(body),
            });
        }

        if (resp && (resp.ok || resp.status === 201)) {
            wrapper.style.display = "none";
            showBtn.style.display = "inline-block";
            await loadTasks();
        } else if (resp) {
            const data = await resp.json();
            const detail = data.detail;
            if (Array.isArray(detail)) {
                alert(detail.map(e => e.msg).join("\n"));
            } else {
                alert(detail || "Failed to save task");
            }
        }
    });
}

function resetTaskForm() {
    document.getElementById("task-id").value = "";
    document.getElementById("task-title").value = "";
    document.getElementById("task-description").value = "";
    document.getElementById("task-status").value = "todo";
    document.getElementById("task-priority").value = "medium";
    document.getElementById("task-due-date").value = "";
    document.getElementById("task-category").value = "";
}

async function editTask(id) {
    const resp = await fetchAPI(`/api/tasks/${id}`);
    if (!resp || !resp.ok) return;
    const t = await resp.json();

    document.getElementById("task-id").value = t.id;
    document.getElementById("task-title").value = t.title;
    document.getElementById("task-description").value = t.description || "";
    document.getElementById("task-status").value = t.status;
    document.getElementById("task-priority").value = t.priority;
    document.getElementById("task-due-date").value = t.due_date || "";
    document.getElementById("task-category").value = t.category_id || "";

    const wrapper = document.getElementById("task-form-wrapper");
    const taskCard = document.querySelector(`[data-task-id="${id}"]`);
    if (taskCard) {
        taskCard.after(wrapper);
    }
    wrapper.style.display = "block";
    document.getElementById("show-add-task").style.display = "none";
    wrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function deleteTask(id) {
    if (!confirm("Are you sure you want to delete this task?")) return;
    const resp = await fetchAPI(`/api/tasks/${id}`, { method: "DELETE" });
    if (resp && (resp.ok || resp.status === 204)) {
        await loadTasks();
    }
}

// ── Filters ─────────────────────────────────────────────────────

function initFilters() {
    const ids = ["filter-status", "filter-priority", "filter-category", "sort-by", "sort-order"];
    ids.forEach(id => {
        document.getElementById(id)?.addEventListener("change", loadTasks);
    });

    let searchTimeout;
    document.getElementById("filter-search")?.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(loadTasks, 300);
    });
}

// ── Init ────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    updateNav();
    initLogout();
    initRegister();
    initLogin();

    // Dashboard-only init
    if (document.getElementById("task-list")) {
        initAddCategory();
        initTaskForm();
        initFilters();
        loadCategories();
        loadTasks();
    }
});
