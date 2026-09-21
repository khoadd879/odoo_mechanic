"""SRE homepage controller.

Renders the public storefront homepage at `/` per brief §19. The page
is data-driven: it pulls the 8 navigation pillars, the homepage seed
industries / applications, and the top three published demo products.

Privacy:
- Reads only `is_published=True sale_ok=True` products.
- Never reads `standard_price`, `product.brand.partner_id`, supplier
  info, or any cost field.

Precedence:
- ``SreHome`` subclasses ``odoo.addons.website.controllers.main.Website``
  and overrides ``index`` so it replaces the default Odoo homepage
  handler at ``/``. Two independent ``@http.route('/')`` declarations
  are not reliable in Odoo 19 — the parent-class override is the
  idiomatic fix and ensures the SRE template wins regardless of
  controller registration order.
"""
from __future__ import annotations

from odoo import http
from odoo.addons.website.controllers.main import Website
from odoo.http import request


class SreHome(Website):
    @http.route()
    def index(self, **kw: object) -> http.Response:
        del kw
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
        featured_products = request.env["product.template"].search(
            request.website.sale_product_domain(),
            order="website_sequence asc, name asc",
            limit=3,
        )
        catalog_preview_products = request.env["product.template"].search(
            request.website.sale_product_domain(),
            order="website_sequence asc, name asc",
            limit=8,
        )
        return request.render(
            "mechanic_workshop.sre_home_page",
            {
                "pillars": pillars,
                "industries": industries,
                "applications": applications,
                "featured_products": featured_products,
                "catalog_preview_products": catalog_preview_products,
            },
        )
