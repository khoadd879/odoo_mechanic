"""SRE catalog page — McMaster-Carr style.

Rendered at ``/sre/catalog``, ``/sre/catalog/pillar/<slug>``,
``/sre/catalog/family/<slug>``. Renders a hand-built catalog that
the SRE visual template builds from scratch, avoiding the
Odoo 19 ``t-elif`` strict-QWeb parser and the Bootstrap 3-col
card grid.
"""
from __future__ import annotations

from odoo import http
from odoo.http import request


class SreCatalog(http.Controller):
    @http.route(
        [
            "/sre/catalog",
            "/sre/catalog/pillar/<string:pillar_slug>",
            "/sre/catalog/family/<string:family_slug>",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def catalog(self, pillar_slug=None, family_slug=None, **kw):
        Pillar = request.env["sre.navigation.pillar"].sudo()
        Family = request.env["sre.product.family"].sudo()
        pillar = Pillar
        family = Family
        if family_slug:
            family = Family.search(
                [("slug", "=", family_slug), ("is_published", "=", True)],
                limit=1,
            )
            if not family:
                return request.not_found()
            pillar = family.pillar_id
        elif pillar_slug:
            pillar = Pillar.search(
                [("slug", "=", pillar_slug), ("is_published", "=", True)],
                limit=1,
            )
            if not pillar:
                return request.not_found()

        # Build the product domain.
        Product = request.env["product.template"]
        base = [("is_published", "=", True), ("sale_ok", "=", True)]
        if family:
            base.append(("family_id", "=", family.id))
        elif pillar:
            base.append(("family_id.pillar_id", "=", pillar.id))

        products = Product.search(base, limit=200, order="name asc")
        products_count = len(products)

        # We render the SRE catalog template directly with a
        # custom layout. We bypass ``website.layout`` entirely
        # because that layout expects a ``main_object`` record
        # we do not have. The SRE template ships its own head
        # and body markup.
        return request.render(
            "mechanic_workshop.sre_catalog_page",
            {
                "products": products,
                "products_count": products_count,
                "search_count": products_count,
                "pillar": pillar,
                "family": family,
                "visible_pillars": request.website.sre_visible_pillars,
                "layout_mode": kw.get("layout_mode", "grid"),
            },
        )