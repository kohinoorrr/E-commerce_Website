/**
 * EcoShop – main.js
 * Client-side interactivity: flash message auto-dismiss, smooth scroll
 */

document.addEventListener("DOMContentLoaded", function () {

    // ── 1. Auto-dismiss flash alerts after 5 s ──────────────────────
    const alerts = document.querySelectorAll(".eco-alert");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── 2. Smooth scroll for anchor links ───────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener("click", function (e) {
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    // ── 3. Product card hover ripple effect ─────────────────────────
    document.querySelectorAll(".product-card").forEach(function (card) {
        card.addEventListener("mouseenter", function () {
            this.style.willChange = "transform";
        });
        card.addEventListener("mouseleave", function () {
            this.style.willChange = "";
        });
    });

    // ── 4. Confirm on destructive admin actions ──────────────────────
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
        el.addEventListener("click", function (e) {
            if (!confirm(this.dataset.confirm)) e.preventDefault();
        });
    });

    // ── 5. Live carbon calculation on cart quantity change ───────────
    // (Forms submit normally; this shows a brief highlight on change)
    document.querySelectorAll(".qty-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const row = this.closest("tr");
            if (row) {
                row.style.transition = "background 0.3s";
                row.style.background = "rgba(22,163,74,0.06)";
                setTimeout(function () { row.style.background = ""; }, 600);
            }
        });
    });

    // ── 6. Tooltip initialization ────────────────────────────────────
    const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipEls.forEach(function (el) {
        new bootstrap.Tooltip(el, { placement: "top" });
    });

});
