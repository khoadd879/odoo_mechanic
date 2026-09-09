/** @odoo-module **/

const SEARCH_SELECTOR = ".sre-global-search";

function clearSuggestions(form) {
    const panel = form.querySelector(".sre-search-suggestions");
    if (panel) {
        panel.hidden = true;
        panel.replaceChildren();
    }
}

function renderSuggestions(form, payload) {
    const panel = form.querySelector(".sre-search-suggestions");
    if (!panel) {
        return;
    }
    panel.replaceChildren();
    for (const tier of payload.tiers || []) {
        const group = document.createElement("div");
        group.className = "sre-search-suggestions__group";

        const label = document.createElement("div");
        label.className = "sre-search-suggestions__label";
        label.textContent = tier.label;
        group.appendChild(label);

        for (const item of tier.items || []) {
            const link = document.createElement("a");
            link.href = item.url;
            link.className = "sre-search-suggestions__item";

            const identity = document.createElement("span");
            identity.className = "sre-search-suggestions__identity";
            identity.textContent = item.name;
            link.appendChild(identity);

            const codes = [item.sku, item.mpn, item.brand].filter(Boolean);
            if (codes.length) {
                const meta = document.createElement("span");
                meta.className = "sre-search-suggestions__meta";
                meta.textContent = codes.join(" · ");
                link.appendChild(meta);
            }
            group.appendChild(link);
        }
        panel.appendChild(group);
    }
    panel.hidden = !panel.childElementCount;
}

function setupSearch(form) {
    const input = form.querySelector('input[name="search"]');
    const endpoint = form.dataset.suggestUrl;
    if (!input || !endpoint) {
        return;
    }

    let timer;
    let requestController;
    input.addEventListener("input", () => {
        window.clearTimeout(timer);
        if (requestController) {
            requestController.abort();
        }
        const term = input.value.trim();
        if (term.length < 2) {
            clearSuggestions(form);
            return;
        }
        timer = window.setTimeout(async () => {
            requestController = new AbortController();
            try {
                const url = `${endpoint}?term=${encodeURIComponent(term)}`;
                const response = await fetch(url, {
                    headers: { Accept: "application/json" },
                    signal: requestController.signal,
                });
                if (response.ok && input.value.trim() === term) {
                    renderSuggestions(form, await response.json());
                }
            } catch (error) {
                if (error.name !== "AbortError") {
                    clearSuggestions(form);
                }
            }
        }, 180);
    });
    input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            clearSuggestions(form);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(SEARCH_SELECTOR).forEach(setupSearch);
    document.addEventListener("click", (event) => {
        document.querySelectorAll(SEARCH_SELECTOR).forEach((form) => {
            if (!form.contains(event.target)) {
                clearSuggestions(form);
            }
        });
    });
});
