/**
 * SRE Technical Catalog - Bidirectional Range Slider / Input Widget
 * Synchronizes dual range sliders with Min/Max numeric input fields.
 */
(function () {
    "use strict";

    function initRangeSliders() {
        var sliderContainers = document.querySelectorAll("[data-range-slider]");
        if (!sliderContainers.length) return;

        sliderContainers.forEach(function (container) {
            var inputMin = container.querySelector(".sre-range-input--min");
            var inputMax = container.querySelector(".sre-range-input--max");
            var sliderMin = container.querySelector(".sre-slider-thumb--min");
            var sliderMax = container.querySelector(".sre-slider-thumb--max");

            if (!inputMin || !inputMax || !sliderMin || !sliderMax) return;

            function syncSliderMin() {
                var valMin = parseFloat(sliderMin.value);
                var valMax = parseFloat(sliderMax.value);
                if (valMin > valMax) {
                    sliderMin.value = valMax;
                    valMin = valMax;
                }
                inputMin.value = valMin;
            }

            function syncSliderMax() {
                var valMin = parseFloat(sliderMin.value);
                var valMax = parseFloat(sliderMax.value);
                if (valMax < valMin) {
                    sliderMax.value = valMin;
                    valMax = valMin;
                }
                inputMax.value = valMax;
            }

            function syncInputMin() {
                if (inputMin.value === "") return;
                var val = parseFloat(inputMin.value);
                if (!isNaN(val)) {
                    var maxBound = parseFloat(sliderMin.max);
                    var minBound = parseFloat(sliderMin.min);
                    if (val >= minBound && val <= maxBound) {
                        sliderMin.value = val;
                    }
                }
            }

            function syncInputMax() {
                if (inputMax.value === "") return;
                var val = parseFloat(inputMax.value);
                if (!isNaN(val)) {
                    var maxBound = parseFloat(sliderMax.max);
                    var minBound = parseFloat(sliderMax.min);
                    if (val >= minBound && val <= maxBound) {
                        sliderMax.value = val;
                    }
                }
            }

            sliderMin.addEventListener("input", syncSliderMin);
            sliderMax.addEventListener("input", syncSliderMax);
            inputMin.addEventListener("input", syncInputMin);
            inputMax.addEventListener("input", syncInputMax);
        });
    }

    function initExpandableRows() {
        document.addEventListener("click", function (e) {
            var btn = e.target.closest(".sre-table-expand-btn");
            if (!btn) return;
            e.preventDefault();
            var targetSelector = btn.getAttribute("data-target");
            if (!targetSelector) return;
            var targetRow = document.querySelector(targetSelector);
            if (!targetRow) return;

            var isHidden = targetRow.classList.contains("d-none");
            targetRow.classList.toggle("d-none");

            var icon = btn.querySelector(".sre-expand-icon");
            var span = btn.querySelector("span:not(.sre-expand-icon)");
            if (isHidden) {
                if (icon) icon.textContent = "▲";
                if (span) span.textContent = "Hide Specs";
            } else {
                if (icon) icon.textContent = "▼";
                if (span) span.textContent = "Technical Detail & CAD";
            }
        });
    }

    function initDetailMultiView() {
        document.addEventListener("click", function (e) {
            var btn = e.target.closest(".sre-detail-view-tab, .sre-detail-thumb-btn");
            if (!btn) return;
            e.preventDefault();
            var targetView = btn.getAttribute("data-view-target");
            if (!targetView) return;

            document.querySelectorAll(".sre-detail-view-tab, .sre-detail-thumb-btn").forEach(function (el) {
                if (el.getAttribute("data-view-target") === targetView) {
                    el.classList.add("is-active");
                } else {
                    el.classList.remove("is-active");
                }
            });

            var views = ["photo", "diagram", "schematic"];
            views.forEach(function (v) {
                var stageEl = document.getElementById("sre-stage-" + v);
                if (stageEl) {
                    if (v === targetView) {
                        stageEl.classList.remove("d-none");
                    } else {
                        stageEl.classList.add("d-none");
                    }
                }
            });
        });
    }

    function initAll() {
        initRangeSliders();
        initExpandableRows();
        initDetailMultiView();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAll);
    } else {
        initAll();
    }
})();
