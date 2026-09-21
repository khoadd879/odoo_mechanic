/**
 * SRE Technical Document Download & Gated Lead Capture (Brief §16 — P1).
 * Handles direct download analytics and gated access modal submission via JSON-RPC.
 */

(() => {
    "use strict";

    document.addEventListener("DOMContentLoaded", () => {
        const modalEl = document.getElementById("sreGatedDocModal");
        if (!modalEl) return;

        const modalDocIdInput = document.getElementById("sreModalDocId");
        const modalDocNameEl = document.getElementById("sreModalDocName");
        const formEl = document.getElementById("sreGatedDocForm");
        const alertEl = document.getElementById("sreGatedModalAlert");
        const submitBtn = document.getElementById("sreGatedSubmitBtn");

        const isVi = document.documentElement.lang && document.documentElement.lang.startsWith("vi");

        // Event delegation for opening the gated modal
        document.addEventListener("click", (event) => {
            const btn = event.target.closest(".sre-btn-gated-download");
            if (!btn) return;
            event.preventDefault();

            const docId = btn.dataset.docId;
            const docName = btn.dataset.docName || "Technical Document";
            const docFormat = btn.dataset.docFormat || "PDF";
            const productName = btn.dataset.productName || "";

            if (modalDocIdInput) modalDocIdInput.value = docId;
            if (modalDocNameEl) {
                modalDocNameEl.textContent = `${docName} (${docFormat})${productName ? ' — ' + productName : ''}`;
            }
            if (alertEl) {
                alertEl.className = "alert d-none mt-3 mb-0 small";
                alertEl.textContent = "";
            }

            // Open modal via bootstrap if available, otherwise manual display
            if (window.bootstrap && window.bootstrap.Modal) {
                const modalInstance = window.bootstrap.Modal.getOrCreateInstance(modalEl);
                modalInstance.show();
            } else {
                modalEl.classList.add("show");
                modalEl.style.display = "block";
            }
        });

        // Form submission via JSON-RPC
        if (formEl) {
            formEl.addEventListener("submit", async (event) => {
                event.preventDefault();

                const formData = new FormData(formEl);
                const payload = {
                    document_id: parseInt(formData.get("document_id") || "0", 10),
                    contact_name: (formData.get("contact_name") || "").toString().trim(),
                    company_name: (formData.get("company_name") || "").toString().trim(),
                    email: (formData.get("email") || "").toString().trim(),
                    phone: (formData.get("phone") || "").toString().trim(),
                    notes: (formData.get("notes") || "").toString().trim(),
                };

                if (!payload.contact_name || !payload.company_name || !payload.email) {
                    showAlert(isVi ? "Vui lòng điền đầy đủ các thông tin bắt buộc." : "Please fill in all required fields.", "danger");
                    return;
                }

                const originalBtnHtml = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = `<i class="fa fa-spinner fa-spin me-1"></i> ${isVi ? "Đang xử lý..." : "Processing..."}`;

                try {
                    const response = await fetch("/sre/document/gated-request", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            jsonrpc: "2.0",
                            method: "call",
                            params: payload,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }

                    const resJson = await response.json();
                    const result = resJson.result || {};

                    if (result.success && result.download_url) {
                        const successMsg = isVi 
                            ? "Xác thực thành công! File đang được tải về máy..." 
                            : "Verified successfully! Your file is downloading...";
                        showAlert(successMsg, "success");

                        // Trigger file download
                        const dlLink = document.createElement("a");
                        dlLink.href = result.download_url;
                        dlLink.setAttribute("download", "");
                        dlLink.target = "_blank";
                        document.body.appendChild(dlLink);
                        dlLink.click();
                        document.body.removeChild(dlLink);

                        // Auto-hide modal after 1.8s
                        setTimeout(() => {
                            if (window.bootstrap && window.bootstrap.Modal) {
                                const modalInstance = window.bootstrap.Modal.getInstance(modalEl);
                                if (modalInstance) modalInstance.hide();
                            } else {
                                modalEl.classList.remove("show");
                                modalEl.style.display = "none";
                            }
                            formEl.reset();
                            if (alertEl) alertEl.className = "alert d-none mt-3 mb-0 small";
                        }, 1800);
                    } else {
                        showAlert(result.error || (isVi ? "Không thể cấp quyền tải tài liệu." : "Could not authorize download."), "danger");
                    }
                } catch (err) {
                    console.error("Gated download error:", err);
                    showAlert(isVi ? "Đã có lỗi xảy ra khi kết nối máy chủ." : "A connection error occurred. Please try again.", "danger");
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHtml;
                }
            });
        }

        function showAlert(message, type) {
            if (!alertEl) return;
            alertEl.className = `alert alert-${type} mt-3 mb-0 small`;
            alertEl.textContent = message;
            alertEl.classList.remove("d-none");
        }
    });
})();
