"""Public Boiler Part Finder Discovery Engine (Brief §11 — P0).

Provides a structured 4-step discovery wizard:
1. Manufacturer -> 2. Boiler Type -> 3. Boiler Model -> 4. Subsystem -> Verified Replacement Parts.
"""

from __future__ import annotations

from odoo import http
from odoo.http import request


class SreBoilerFinder(http.Controller):
    """Boiler Part Discovery Engine."""

    @http.route(
        [
            "/boiler-finder",
            "/sre/boiler-finder",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def boiler_finder(
        self,
        make: str | None = None,
        type: str | None = None,
        model: str | None = None,
        subsystem: str | None = None,
        **kw: object,
    ) -> http.Response:
        """Render the 4-step interactive Boiler Part Finder."""
        BoilerMfg = request.env["sre.boiler.manufacturer"].sudo()
        BoilerType = request.env["sre.boiler.type"].sudo()
        BoilerModel = request.env["sre.boiler.model"].sudo()
        BoilerSubsystem = request.env["sre.boiler.subsystem"].sudo()
        BoilerMapping = request.env["sre.boiler.part.mapping"].sudo()

        manufacturers = BoilerMfg.search([("active", "=", True)])

        selected_make = BoilerMfg
        if make:
            selected_make = BoilerMfg.search(
                [("slug", "=", make), ("active", "=", True)], limit=1
            )

        available_types = BoilerType
        available_models = BoilerModel
        if selected_make:
            available_models = BoilerModel.search(
                [("manufacturer_id", "=", selected_make.id), ("active", "=", True)]
            )
            available_types = available_models.mapped("boiler_type_id").filtered("active")

        selected_type = BoilerType
        if type and selected_make:
            selected_type = BoilerType.search(
                [("slug", "=", type), ("active", "=", True)], limit=1
            )
            if selected_type:
                available_models = available_models.filtered(
                    lambda m: m.boiler_type_id.id == selected_type.id
                )

        selected_model = BoilerModel
        if model and selected_make:
            selected_model = BoilerModel.search(
                [
                    ("slug", "=", model),
                    ("manufacturer_id", "=", selected_make.id),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if selected_model and not selected_type:
                selected_type = selected_model.boiler_type_id

        available_subsystems = BoilerSubsystem
        mapped_parts = []
        selected_subsystem = BoilerSubsystem

        if selected_model:
            model_mappings = BoilerMapping.search(
                [("boiler_model_id", "=", selected_model.id)]
            )
            available_subsystems = model_mappings.mapped("subsystem_id").filtered("active")

            if subsystem:
                selected_subsystem = BoilerSubsystem.search(
                    [("slug", "=", subsystem), ("active", "=", True)], limit=1
                )
                if selected_subsystem:
                    model_mappings = model_mappings.filtered(
                        lambda item: item.subsystem_id.id == selected_subsystem.id
                    )

            published_mappings = model_mappings.filtered(
                lambda item: item.product_tmpl_id.is_published
                and item.product_tmpl_id.sale_ok
            )
            mapped_parts = published_mappings.sorted(
                lambda item: (not item.is_critical_spare, item.sequence, item.id)
            )

        current_step = 1
        if selected_subsystem:
            current_step = 5
        elif selected_model:
            current_step = 4
        elif selected_make:
            current_step = 2 if len(available_types) > 1 and not selected_type else 3

        return request.render(
            "mechanic_workshop.sre_boiler_finder_page",
            {
                "manufacturers": manufacturers,
                "selected_make": selected_make,
                "available_types": available_types,
                "selected_type": selected_type,
                "available_models": available_models,
                "selected_model": selected_model,
                "available_subsystems": available_subsystems,
                "selected_subsystem": selected_subsystem,
                "mapped_parts": mapped_parts,
                "current_step": current_step,
            },
        )

    @http.route(
        "/sre/boiler-finder/api/options",
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def boiler_finder_api(
        self,
        make_slug: str | None = None,
        model_slug: str | None = None,
    ) -> dict:
        """Return available cascade options for interactive client selection."""
        data = {"types": [], "models": [], "subsystems": []}

        if make_slug:
            make = (
                request.env["sre.boiler.manufacturer"]
                .sudo()
                .search([("slug", "=", make_slug), ("active", "=", True)], limit=1)
            )
            if make:
                models_rec = request.env["sre.boiler.model"].sudo().search(
                    [("manufacturer_id", "=", make.id), ("active", "=", True)]
                )
                data["models"] = [
                    {"id": m.id, "name": m.name, "slug": m.slug} for m in models_rec
                ]
                types_rec = models_rec.mapped("boiler_type_id").filtered("active")
                data["types"] = [
                    {"id": t.id, "name": t.name, "slug": t.slug} for t in types_rec
                ]

        if model_slug:
            model = (
                request.env["sre.boiler.model"]
                .sudo()
                .search([("slug", "=", model_slug), ("active", "=", True)], limit=1)
            )
            if model:
                mappings = (
                    request.env["sre.boiler.part.mapping"]
                    .sudo()
                    .search([("boiler_model_id", "=", model.id)])
                )
                subsystems = mappings.mapped("subsystem_id").filtered("active")
                data["subsystems"] = [
                    {
                        "id": s.id,
                        "name": s.name,
                        "slug": s.slug,
                        "icon": s.icon,
                    }
                    for s in subsystems
                ]

        return data
