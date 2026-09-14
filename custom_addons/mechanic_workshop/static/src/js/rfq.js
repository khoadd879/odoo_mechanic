(() => {
    document.addEventListener("submit", async (event) => {
        const form = event.target.closest("form.sre-rfq-add");
        if (!form) return;
        event.preventDefault();
        if (form.dataset.busy === "1") return;
        form.dataset.busy = "1";
        const button = form.querySelector('button[type="submit"]');
        const feedback = form.querySelector(".sre-rfq-feedback");
        const originalButtonHtml = button ? button.innerHTML : "";
        if (button) button.disabled = true;
        if (feedback) feedback.textContent = "";
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
            if (feedback) {
                feedback.className = "sre-rfq-feedback mt-1 text-success";
                feedback.textContent = feedback.dataset.success || "Added to RFQ!";
            }
            if (button) {
                button.innerHTML = '<i class="fa fa-check" aria-hidden="true"></i> Added!';
                button.classList.add("sre-button--added");
                setTimeout(() => {
                    button.innerHTML = originalButtonHtml;
                    button.classList.remove("sre-button--added");
                }, 2500);
            }
        } catch {
            if (feedback) {
                feedback.className = "sre-rfq-feedback mt-1 text-danger";
                feedback.textContent = feedback.dataset.error || "Could not add to RFQ";
            }
            if (button) {
                button.innerHTML = originalButtonHtml;
            }
        } finally {
            if (button) button.disabled = false;
            delete form.dataset.busy;
        }
    });
})();
