"""Tiered public autocomplete for SRE catalogue searches."""

from __future__ import annotations

from odoo import http
from odoo.fields import Domain
from odoo.http import request


class SreSearchSuggest(http.Controller):
    """Return exact part-number matches before generic keywords."""

    PER_TIER = 5
    MIN_LEN = 2

    @staticmethod
    def _serialize(records, seen_ids: set[int]) -> list[dict[str, object]]:
        """Serialize public product identity fields without duplicates."""

        items: list[dict[str, object]] = []
        for product in records:
            if product.id in seen_ids:
                continue
            seen_ids.add(product.id)
            items.append(
                {
                    "id": product.id,
                    "name": product.display_name,
                    "url": product.website_url,
                    "brand": product.product_brand_id.name or False,
                    "sku": product.default_code or False,
                    "mpn": product.manufacturer_pref or False,
                }
            )
        return items

    @http.route(
        ["/shop/search_suggest", "/sre/search_suggest"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
        csrf=False,
    )
    def suggest(self, term: str | None = None, **kw: object) -> http.Response:
        """Return exact SKU/MPN/OEM/Brand tiers and a keyword tier."""

        del kw
        term = str(term or "").strip()[:160]
        if len(term) < self.MIN_LEN:
            return request.make_json_response({"term": term, "tiers": []})

        Product = request.env["product.template"].sudo()
        base = Domain(request.website.sale_product_domain())
        lang = request.env.context.get("lang") or ""
        is_vi = lang.startswith("vi")
        tier_domains = (
            ("SKU", Domain("default_code", "=ilike", term)),
            ("MPN", Domain("manufacturer_pref", "=ilike", term)),
            (
                "Mã OEM" if is_vi else "OEM PN",
                Domain("sre_public_oem_part_numbers", "=ilike", term)
                | Domain("sre_public_oem_part_numbers", "ilike", term),
            ),
            ("Thương hiệu" if is_vi else "Brand", Domain("product_brand_id.name", "=ilike", term)),
            (
                "Từ khóa" if is_vi else "Keyword",
                Domain.OR(
                    [
                        Domain("name", "ilike", term),
                        Domain("default_code", "ilike", term),
                        Domain("manufacturer_pref", "ilike", term),
                        Domain("manufacturer_public_name", "ilike", term),
                        Domain("product_brand_id.name", "ilike", term),
                        Domain("sre_public_oem_part_numbers", "ilike", term),
                        Domain("description_sale", "ilike", term),
                        Domain("description", "ilike", term),
                    ]
                ),
            ),
        )
        seen_ids: set[int] = set()
        tiers = []
        for label, tier_domain in tier_domains:
            records = Product.search(
                base & tier_domain,
                limit=self.PER_TIER + len(seen_ids),
                order="website_sequence asc, name asc, id asc",
            )
            items = self._serialize(records, seen_ids)[: self.PER_TIER]
            if items:
                tiers.append({"label": label, "items": items})

        return request.make_json_response({"term": term, "tiers": tiers})
