// Placeholder — full logic comes in Day 6.
// For now: toggle nav links based on token presence.

document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    const navLinks = document.getElementById("nav-links");
    const navAuth = document.getElementById("nav-auth");

    if (token) {
        if (navLinks) navLinks.style.display = "none";
        if (navAuth) navAuth.style.display = "flex";
    }

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("token");
            window.location.href = "/login";
        });
    }
});
