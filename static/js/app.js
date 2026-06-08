window.ONEDELUX = (() => {
    const frNumber = new Intl.NumberFormat("fr-FR");
    const frPercent = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1, minimumFractionDigits: 1 });

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function toQuery(params = {}) {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== "") {
                query.set(key, value);
            }
        });
        const queryString = query.toString();
        return queryString ? `?${queryString}` : "";
    }

    async function apiRequest(path, { method = "GET", body = null } = {}) {
        const response = await fetch(path, {
            method,
            headers: body ? { "Content-Type": "application/json" } : undefined,
            body: body ? JSON.stringify(body) : undefined,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload.error || payload.message || `HTTP ${response.status}`);
        }
        return payload;
    }

    const apiGet = (path, params = {}) => apiRequest(`${path}${toQuery(params)}`);
    const apiPost = (path, body = null) => apiRequest(path, { method: "POST", body });
    const apiDelete = (path) => apiRequest(path, { method: "DELETE" });

    function formatDateTime(timestamp) {
        if (!timestamp) return "N/A";
        const date = new Date(timestamp * 1000);
        return date.toLocaleString("fr-FR", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function formatDate(timestamp) {
        if (!timestamp) return "N/A";
        return new Date(timestamp * 1000).toLocaleDateString("fr-FR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        });
    }

    function formatPercent(value) {
        if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
        return `${frPercent.format(Number(value) * 100)}%`;
    }

    function formatCount(value) {
        return frNumber.format(Number(value || 0));
    }

    function normalizeStatus(value) {
        if (typeof value === "boolean") {
            return value ? "live" : "upcoming";
        }

        const normalized = String(value ?? "").trim().toLowerCase();
        if (!normalized) return "upcoming";
        if (["live", "en direct"].includes(normalized)) return "live";
        if (["upcoming", "a venir", "? venir"].includes(normalized)) return "upcoming";
        if (["finished", "termine", "termin?", "final", "ended"].includes(normalized)) return "finished";
        return normalized;
    }

    function statusLabel(value) {
        switch (normalizeStatus(value)) {
            case "live":
                return "EN DIRECT";
            case "finished":
                return "TERMIN?";
            default:
                return "À VENIR";
        }
    }

    function statusPill(value) {
        const status = normalizeStatus(value);
        if (status === "live") {
            return `<span class="pill pill-live"><i class="fa-solid fa-circle"></i> ${statusLabel(status)}</span>`;
        }
        if (status === "finished") {
            return `<span class="pill pill-finished"><i class="fa-solid fa-square-check"></i> ${statusLabel(status)}</span>`;
        }
        return `<span class="pill pill-upcoming"><i class="fa-regular fa-clock"></i> ${statusLabel(status)}</span>`;
    }

    function isLiveStatus(value) {
        return normalizeStatus(value) === "live";
    }

    function isUpcomingStatus(value) {
        return normalizeStatus(value) === "upcoming";
    }

    function isFinishedStatus(value) {
        return normalizeStatus(value) === "finished";
    }

    function normalizePredictionValue(value, event) {
        if (value === "team1") return event?.team1_name || "Team 1";
        if (value === "team2") return event?.team2_name || "Team 2";
        if (value === "home") return event?.team1_name || "Home";
        if (value === "away") return event?.team2_name || "Away";
        if (typeof value === "boolean") return value ? "OVER" : "UNDER";
        return value;
    }

    function confidenceClass(confidence) {
        const value = Number(confidence || 0);
        if (value >= 0.7) return "confidence-high";
        if (value >= 0.5) return "confidence-medium";
        return "confidence-low";
    }

    return {
        apiGet,
        apiPost,
        apiRequest,
        apiDelete,
        escapeHtml,
        formatDateTime,
        formatDate,
        formatPercent,
        formatCount,
        normalizeStatus,
        statusLabel,
        statusPill,
        isLiveStatus,
        isUpcomingStatus,
        isFinishedStatus,
        normalizePredictionValue,
        confidenceClass,
    };
})();
