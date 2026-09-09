"""SRE homepage controller.

Renders the public storefront homepage at `/` per brief §19. The page
is data-driven: it pulls the 8 navigation pillars, the homepage seed
industries / applications, and the top three published demo products.

Privacy:
- Reads only `is_published=True sale_ok=True` products.
- Never reads `standard_price`, `product.brand.partner_id`, supplier
  info, or any cost field.
"""
from __future__ import annotations

from odoo import http
from odoo.http import request


class SreHome(http.Controller):
    @http.route(
        "/",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def home(self, **kw):
        pillars = request.website.sre_visible_pillars
        industries = (
            request.env["sre.industry"]
            .sudo()
            .search([("active", "=", True)], order="sequence, name", limit=4)
        )
        applications = (
            request.env["sre.application"]
            .sudo()
            .search([("active", "=", True)], order="sequence, name", limit=3)
        )
        featured_products = (
            request.env["product.template"]
            .sudo()
            .search(
                [("is_published", "=", True), ("sale_ok", "=", True)],
                order="website_sequence asc, name asc",
                limit=3,
            )
        )
        return request.render(
            "mechanic_workshop.sre_home_page",
            {
                "pillars": pillars,
                "industries": industries,
                "applications": applications,
                "featured_products": featured_products,
            },
        )
