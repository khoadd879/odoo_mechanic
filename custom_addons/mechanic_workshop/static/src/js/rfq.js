(() => {
    document.addEventListener("submit", async (event) => {
        const form = event.target.closest("form.sre-rfq-add");
        if (!form) return;
        event.preventDefault();
        if (form.dataset.busy === "1") return;
        form.dataset.busy = "1";
        const button = form.querySelector('button[type="submit"]');
        const feedback = form.querySelector(".sre-rfq-feedback");
        button.disabled = true;
        feedback.textContent = "";
        try {
            const data = new FormData(form);
            data.set("ajax", "1");
            const response = await fetch(form.action, {
                method: "POST", body: data, credentials: "same-origin",
            });
            if (!response.ok) throw new Error("RFQ request failed");
            const result = await response.json();
            document.querySelectorAll(".sre-rfq-count").forEach((badge) => {
                badge.textContent = String(result.line_count);
            });
            feedback.className = "sre-rfq-feedback mt-3 text-success";
            feedback.textContent = feedback.dataset.success;
        } catch {
            feedback.className = "sre-rfq-feedback mt-3 text-danger";
            feedback.textContent = feedback.dataset.error;
        } finally {
            button.disabled = false;
            delete form.dataset.busy;
        }
    });
})();
