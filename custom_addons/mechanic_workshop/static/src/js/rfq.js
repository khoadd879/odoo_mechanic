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
        const isVi = document.documentElement.lang && document.documentElement.lang.startsWith("vi");
        const addedText = isVi ? "Đã thêm!" : "Added!";
        const defaultSuccess = isVi ? "Đã thêm vào danh sách RFQ!" : "Added to RFQ!";
        const defaultError = isVi ? "Không thể thêm vào RFQ" : "Could not add to RFQ";
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
                feedback.textContent = (isVi ? feedback.dataset.successVi : feedback.dataset.success) || defaultSuccess;
            }
            if (button) {
                button.innerHTML = '<i class="fa fa-check" aria-hidden="true"></i> ' + addedText;
                button.classList.add("sre-button--added");
                setTimeout(() => {
                    button.innerHTML = originalButtonHtml;
                    button.classList.remove("sre-button--added");
                }, 2500);
            }
        } catch {
            if (feedback) {
                feedback.className = "sre-rfq-feedback mt-1 text-danger";
                feedback.textContent = (isVi ? feedback.dataset.errorVi : feedback.dataset.error) || defaultError;
            }
            if (button) {
                button.innerHTML = originalButtonHtml;
            }
        } finally {
            if (button) button.disabled = false;
            delete form.dataset.busy;
        }
    });

    // BOM Quick Add / Paste handler
    document.addEventListener("submit", async (event) => {
        const form = event.target.closest("#sreBomPasteForm");
        if (!form) return;
        event.preventDefault();

        const textarea = form.querySelector("textarea[name='bom_text']");
        const btn = form.querySelector("button[type='submit']");
        const feedback = form.querySelector("#sreBomFeedback");
        if (!textarea || !textarea.value.trim()) return;

        const isVi = document.documentElement.lang && document.documentElement.lang.startsWith("vi");
        const origBtnText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<i class="fa fa-spinner fa-spin me-1"></i> ${isVi ? "Đang xử lý..." : "Parsing..."}`;
        if (feedback) feedback.className = "d-none";

        try {
            const response = await fetch("/rfq/api/bom-parse", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: { text: textarea.value },
                }),
            });
            if (!response.ok) throw new Error("HTTP error");
            const resJson = await response.json();
            const result = resJson.result || {};

            if (result.success) {
                let msg = isVi 
                    ? `Đã thêm thành công ${result.added_count} mã vật tư vào RFQ.` 
                    : `Successfully added ${result.added_count} part(s) to RFQ.`;
                if (result.unmatched_count > 0) {
                    msg += isVi
                        ? ` Có ${result.unmatched_count} mã không tìm thấy trong danh mục.`
                        : ` ${result.unmatched_count} part(s) could not be matched.`;
                }
                if (feedback) {
                    feedback.className = "alert alert-success mt-2 p-2 small";
                    feedback.innerHTML = msg + (result.added_count > 0 ? (isVi ? " <br/>Đang làm mới trang..." : " <br/>Reloading...") : "");
                }
                if (result.added_count > 0) {
                    setTimeout(() => window.location.reload(), 1200);
                }
            } else {
                if (feedback) {
                    feedback.className = "alert alert-danger mt-2 p-2 small";
                    feedback.textContent = result.error || "Error parsing BOM.";
                }
            }
        } catch (e) {
            if (feedback) {
                feedback.className = "alert alert-danger mt-2 p-2 small";
                feedback.textContent = isVi ? "Lỗi kết nối máy chủ." : "Server connection error.";
            }
        } finally {
            btn.disabled = false;
            btn.innerHTML = origBtnText;
        }
    });

    document.addEventListener("submit", async function (e) {
        const form = e.target.closest("#sreBomUploadForm");
        if (!form) return;
        e.preventDefault();

        const fileInput = form.querySelector("input[name='bom_file']");
        const btn = form.querySelector("button[type='submit']");
        const feedback = form.querySelector("#sreBomUploadFeedback");
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;

        const isVi = document.documentElement.lang && document.documentElement.lang.startsWith("vi");
        const origBtnText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<i class="fa fa-spinner fa-spin me-1"></i> ${isVi ? "Đang tải & xử lý..." : "Uploading & parsing..."}`;
        if (feedback) feedback.className = "d-none";

        try {
            const formData = new FormData(form);
            const response = await fetch("/rfq/api/bom-upload", {
                method: "POST",
                body: formData,
            });
            if (!response.ok) throw new Error("HTTP error");
            const result = await response.json();

            if (result.success) {
                let msg = isVi 
                    ? `Đã nhận diện và thêm thành công ${result.added_count} mã vật tư từ file Excel vào RFQ.` 
                    : `Successfully recognized and added ${result.added_count} part(s) from spreadsheet to RFQ.`;
                if (result.unmatched_count > 0) {
                    msg += isVi
                        ? ` Có ${result.unmatched_count} mã không tìm thấy trong danh mục.`
                        : ` ${result.unmatched_count} part(s) could not be matched.`;
                }
                if (feedback) {
                    feedback.className = "alert alert-success mt-2 p-2 small";
                    feedback.innerHTML = msg + (result.added_count > 0 ? (isVi ? " <br/>Đang làm mới trang..." : " <br/>Reloading...") : "");
                }
                if (result.added_count > 0) {
                    setTimeout(() => window.location.reload(), 1200);
                }
            } else {
                if (feedback) {
                    feedback.className = "alert alert-danger mt-2 p-2 small";
                    feedback.textContent = result.error || (isVi ? "Lỗi phân tích file Excel." : "Error parsing spreadsheet file.");
                }
            }
        } catch (e) {
            if (feedback) {
                feedback.className = "alert alert-danger mt-2 p-2 small";
                feedback.textContent = isVi ? "Lỗi kết nối máy chủ khi tải file." : "Server connection error during upload.";
            }
        } finally {
            btn.disabled = false;
            btn.innerHTML = origBtnText;
        }
    });
})();

