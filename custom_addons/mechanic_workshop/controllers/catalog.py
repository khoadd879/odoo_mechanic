"""Public SRE technical catalog.

The catalog is intentionally separate from Odoo's retail ``/shop`` grid,
but it reuses the native website product domain and ``website.layout``.
This keeps publication, website and company rules native while presenting
the dense RFQ-first catalogue required by the SRE brief.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from urllib.parse import urlencode

from odoo import http
from odoo.fields import Domain
from odoo.http import request


class SreCatalog(http.Controller):
    """Render searchable, filterable catalogue pages."""

    PAGE_SIZES = (12, 24, 48)
    SORT_ORDERS = {
        "relevance": "website_sequence asc, name asc, id asc",
        "name_asc": "name asc, id asc",
        "name_desc": "name desc, id desc",
    }
    SEARCH_FIELDS = (
        "name",
        "default_code",
        "variants_default_code",
        "barcode",
        "manufacturer_pref",
        "manufacturer_public_name",
        "product_brand_id.name",
        "sre_public_oem_part_numbers",
        "description_sale",
        "description",
    )
    EXACT_FIELDS = (
        "default_code",
        "variants_default_code",
        "barcode",
        "manufacturer_pref",
        "product_brand_id.name",
        "sre_public_oem_part_numbers",
    )

    @staticmethod
    def _text(value: object, limit: int = 160) -> str:
        """Return a bounded query-string value."""

        return str(value or "").strip()[:limit]

    @staticmethod
    def _positive_int(value: object, default: int = 1) -> int:
        """Coerce a query-string value to a positive integer."""

        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _query_url(base_path: str, **updates: object) -> str:
        """Build a catalogue URL while preserving active filters."""

        allowed = {
            "search",
            "layout_mode",
            "order",
            "per_page",
            "page",
            "industry",
            "application",
            "brand",
            "attr",
        }
        params: dict[str, list[str]] = {}
        for key in allowed:
            values = request.httprequest.args.getlist(key)
            if values:
                params[key] = [str(value) for value in values]

        for key, value in updates.items():
            if key not in allowed:
                continue
            if value in (None, False, "") or (key == "page" and value == 1):
                params.pop(key, None)
            elif isinstance(value, (list, tuple, set)):
                params[key] = [str(item) for item in value]
            else:
                params[key] = [str(value)]

        query = urlencode(params, doseq=True)
        return f"{base_path}?{query}" if query else base_path

    @classmethod
    def _search_domain(cls, search: str) -> Domain:
        """Build native ORM search semantics for every search term."""

        domain = Domain.TRUE
        for term in search.split():
            domain &= Domain.OR(
                [Domain(field_name, "ilike", term) for field_name in cls.SEARCH_FIELDS]
            )
        return domain

    @classmethod
    def _exact_domain(cls, search: str) -> Domain:
        """Match exact public part identifiers for relevance ranking."""

        if not search:
            return Domain.FALSE
        return Domain.OR(
            [Domain(field_name, "=ilike", search) for field_name in cls.EXACT_FIELDS]
        )

    @http.route(
        [
            "/sre/catalog",
            "/sre/catalog/page/<int:page>",
            "/sre/catalog/pillar/<string:pillar_slug>",
            "/sre/catalog/pillar/<string:pillar_slug>/page/<int:page>",
            "/sre/catalog/family/<string:family_slug>",
            "/sre/catalog/family/<string:family_slug>/page/<int:page>",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def catalog(
        self,
        page: int | str = 1,
        pillar_slug: str | None = None,
        family_slug: str | None = None,
        **kw: object,
    ) -> http.Response:
        """Render the catalogue with real search, filters and pagination."""

        Pillar = request.env["sre.navigation.pillar"].sudo()
        Family = request.env["sre.product.family"].sudo()
        pillar = Pillar
        family = Family
        if family_slug:
            family = Family.search(
                [
                    ("slug", "=", family_slug),
                    ("is_published", "=", True),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if not family:
                return request.not_found()
            pillar = family.pillar_id
        elif pillar_slug:
            pillar = Pillar.search(
                [
                    ("slug", "=", pillar_slug),
                    ("is_published", "=", True),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if not pillar:
                return request.not_found()

        base_path = "/sre/catalog"
        if family:
            base_path = f"{base_path}/family/{family.slug}"
        elif pillar:
            base_path = f"{base_path}/pillar/{pillar.slug}"
        query_url: Callable[..., str] = lambda **updates: self._query_url(
            base_path, **updates
        )

        search = self._text(kw.get("search"))
        layout_mode = self._text(kw.get("layout_mode"), 12)
        if layout_mode not in {"grid", "list", "table"}:
            layout_mode = "list"
        sort_key = self._text(kw.get("order"), 24)
        if sort_key not in self.SORT_ORDERS:
            sort_key = "relevance" if search else "name_asc"
        per_page = self._positive_int(kw.get("per_page"), 12)
        if per_page not in self.PAGE_SIZES:
            per_page = 12
        current_page = self._positive_int(page, 1)

        Product = request.env["product.template"]
        domain = Domain(request.website.sale_product_domain())
        if family:
            domain &= Domain("family_id", "=", family.id)
        elif pillar:
            domain &= Domain("family_id.pillar_id", "=", pillar.id)

        industry_slug = self._text(kw.get("industry"), 80)
        application_slug = self._text(kw.get("application"), 80)
        industry = request.env["sre.industry"].sudo()
        application = request.env["sre.application"].sudo()
        if industry_slug:
            industry = industry.search(
                [("slug", "=", industry_slug), ("active", "=", True)], limit=1
            )
            domain &= (
                Domain("industry_ids", "in", industry.id)
                if industry
                else Domain.FALSE
            )
        if application_slug:
            application = application.search(
                [("slug", "=", application_slug), ("active", "=", True)],
                limit=1,
            )
            domain &= (
                Domain("application_ids", "in", application.id)
                if application
                else Domain.FALSE
            )

        try:
            brand_id = max(int(kw.get("brand") or 0), 0)
        except (TypeError, ValueError):
            brand_id = 0
        available_brands = (
            Product.search(request.website.sale_product_domain())
            .mapped("product_brand_id")
            .sorted(lambda item: (item.name or "", item.id))
        )
        brand = request.env["product.brand"]
        if brand_id:
            brand = available_brands.filtered(lambda item: item.id == brand_id)
            domain &= Domain("product_brand_id", "=", brand.id) if brand else Domain.FALSE

        selected_attributes: dict[int, set[int]] = {}
        for raw_value in request.httprequest.args.getlist("attr"):
            try:
                attribute_id, value_id = (int(item) for item in raw_value.split("-", 1))
            except (TypeError, ValueError):
                continue
            selected_attributes.setdefault(attribute_id, set()).add(value_id)

        filter_lines: list[dict[str, object]] = []
        valid_attributes: dict[int, set[int]] = {}
        if family and family.attribute_profile_id:
            for line in family.attribute_profile_id.sudo().line_ids.filtered(
                "is_filter_shown"
            ):
                values = line.value_ids or line.attribute_id.value_ids
                value_ids = set(values.ids)
                valid_attributes[line.attribute_id.id] = value_ids
                filter_lines.append(
                    {
                        "attribute": line.attribute_id,
                        "values": values,
                    }
                )
        selected_attributes = {
            attribute_id: value_ids & valid_attributes[attribute_id]
            for attribute_id, value_ids in selected_attributes.items()
            if attribute_id in valid_attributes
            and value_ids & valid_attributes[attribute_id]
        }
        for value_ids in selected_attributes.values():
            domain &= Domain("attribute_line_ids.value_ids", "in", list(value_ids))

        if brand:
            domain &= Domain("product_brand_id", "=", brand.id)
        if search:
            domain &= self._search_domain(search)

        products_count = Product.search_count(domain)
        total_pages = max(1, math.ceil(products_count / per_page))
        current_page = min(current_page, total_pages)
        offset = (current_page - 1) * per_page
        order = self.SORT_ORDERS[sort_key]

        if search and sort_key == "relevance":
            exact_match = self._exact_domain(search)
            exact_domain = domain & exact_match
            exact_count = Product.search_count(exact_domain)
            if offset < exact_count:
                exact_products = Product.search(
                    exact_domain, offset=offset, limit=per_page, order=order
                )
                remaining_limit = per_page - len(exact_products)
                remaining_products = Product
                if remaining_limit:
                    remaining_products = Product.search(
                        domain & ~exact_match,
                        limit=remaining_limit,
                        order=order,
                    )
                products = exact_products + remaining_products
            else:
                products = Product.search(
                    domain & ~exact_match,
                    offset=offset - exact_count,
                    limit=per_page,
                    order=order,
                )
        else:
            products = Product.search(
                domain, offset=offset, limit=per_page, order=order
            )

        page_start = offset + 1 if products else 0
        page_end = offset + len(products)
        page_window_start = max(1, current_page - 2)
        page_window_end = min(total_pages, current_page + 2)
        pager_pages = list(range(page_window_start, page_window_end + 1))
        families = Family
        if pillar:
            families = Family.search(
                [
                    ("pillar_id", "=", pillar.id),
                    ("is_published", "=", True),
                    ("active", "=", True),
                ],
                order="sequence, name",
            )

        return request.render(
            "mechanic_workshop.sre_catalog_page",
            {
                "products": products,
                "products_count": products_count,
                "page_start": page_start,
                "page_end": page_end,
                "current_page": current_page,
                "total_pages": total_pages,
                "pager_pages": pager_pages,
                "per_page": per_page,
                "page_sizes": self.PAGE_SIZES,
                "pillar": pillar,
                "family": family,
                "families": families,
                "industry": industry,
                "application": application,
                "brands": available_brands,
                "brand": brand,
                "filter_lines": filter_lines,
                "selected_attribute_keys": {
                    f"{attribute_id}-{value_id}"
                    for attribute_id, value_ids in selected_attributes.items()
                    for value_id in value_ids
                },
                "visible_pillars": request.website.sre_visible_pillars,
                "search": search,
                "layout_mode": layout_mode,
                "sort_key": sort_key,
                "base_path": base_path,
                "query_url": query_url,
            },
        )
