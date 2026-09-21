"""SRE Cross Reference Engine Controller (Brief §12 — P0).

Provides dedicated search and lookup for competitor and OEM part numbers,
mapping them to verified SRE replacement components with engineering notes.
"""

from __future__ import annotations

from odoo import http
from odoo.http import request


class SreCrossReferenceController(http.Controller):
    """Public cross-reference lookup and search controller."""

    @http.route(
        ["/cross-reference", "/sre/cross-reference"],
        type="http",
        auth="public",
        website=True,
    )
    def cross_reference_search(
        self,
        q: str | None = None,
        brand: str | None = None,
        grade: str | None = None,
        **kwargs,
    ) -> http.Response:
        """Render cross-reference discovery page with filtering."""
        domain = [("active", "=", True)]

        q_clean = (q or "").strip()
        if q_clean:
            domain.extend(
                [
                    "|",
                    ("source_part_number", "ilike", q_clean),
                    ("source_brand", "ilike", q_clean),
                ]
            )

        brand_clean = (brand or "").strip()
        if brand_clean:
            domain.append(("source_brand", "=", brand_clean))

        grade_clean = (grade or "").strip()
        if grade_clean in ("direct", "drop_in", "obsolete"):
            domain.append(("replacement_type", "=", grade_clean))

        cross_refs = (
            request.env["sre.product.cross.reference"]
            .sudo()
            .search(domain, order="source_brand, source_part_number")
        )

        # Aggregate available brands for quick filter pills
        all_refs = request.env["sre.product.cross.reference"].sudo().search([("active", "=", True)])
        available_brands = sorted(list(set(all_refs.mapped("source_brand"))))

        # Grade counts
        counts = {
            "all": len(cross_refs),
            "direct": len(cross_refs.filtered(lambda r: r.replacement_type == "direct")),
            "drop_in": len(cross_refs.filtered(lambda r: r.replacement_type == "drop_in")),
            "obsolete": len(cross_refs.filtered(lambda r: r.replacement_type == "obsolete")),
        }

        values = {
            "query": q_clean,
            "selected_brand": brand_clean,
            "selected_grade": grade_clean,
            "cross_refs": cross_refs,
            "available_brands": available_brands,
            "counts": counts,
        }
        return request.render("mechanic_workshop.sre_cross_reference_page", values)

    @http.route(
        "/sre/cross-reference/api/search",
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def cross_reference_api(self, q: str = "") -> dict:
        """Typeahead search endpoint returning matching cross references."""
        q_clean = (q or "").strip()
        if not q_clean or len(q_clean) < 2:
            return {"results": []}

        domain = [
            ("active", "=", True),
            "|",
            ("source_part_number", "ilike", q_clean),
            ("source_brand", "ilike", q_clean),
        ]
        records = (
            request.env["sre.product.cross.reference"]
            .sudo()
            .search(domain, limit=8, order="source_brand, source_part_number")
        )

        results = []
        for r in records:
            prod = r.target_product_id
            results.append(
                {
                    "id": r.id,
                    "source_part_number": r.source_part_number,
                    "source_brand": r.source_brand,
                    "source_specs": r.source_specs or "",
                    "replacement_type": r.replacement_type,
                    "replacement_type_label": dict(
                        r._fields["replacement_type"].selection
                    ).get(r.replacement_type, r.replacement_type),
                    "product_id": prod.id,
                    "product_name": prod.name,
                    "product_sku": prod.default_code or "",
                    "product_url": prod.website_url,
                }
            )
        return {"results": results}
