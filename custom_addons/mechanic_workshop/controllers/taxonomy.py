"""Controllers for SRE Industry and Application landing pages.

Per Brief §14 & §15:
- Industry and Application are independent taxonomies from product categories.
- Dedicated landing pages provide engineering context, system duty specifications,
  and mapped products with direct RFQ actions.
"""

from __future__ import annotations

from odoo import http
from odoo.fields import Domain
from odoo.http import request


class SreTaxonomy(http.Controller):
    """Render specialized Industry and Application landing pages."""

    # -------------------------------------------------------------------------
    # Industry Routes
    # -------------------------------------------------------------------------

    @http.route(
        ["/sre/industry", "/sre/industry/"],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def industry_index(self, **kw: object) -> http.Response:
        """Render the directory of all published SRE industries."""
        del kw
        industries = (
            request.env["sre.industry"]
            .sudo()
            .search([("active", "=", True)], order="sequence, name")
        )
        return request.render(
            "mechanic_workshop.sre_industry_index",
            {
                "industries": industries,
            },
        )

    @http.route(
        "/sre/industry/<string:industry_slug>",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def industry_detail(
        self, industry_slug: str, **kw: object
    ) -> http.Response:
        """Render the specialized landing page for an industry."""
        del kw
        industry = (
            request.env["sre.industry"]
            .sudo()
            .search(
                [("slug", "=", industry_slug), ("active", "=", True)], limit=1
            )
        )
        if not industry:
            return request.not_found()

        # Fetch published products mapped to this industry
        domain = Domain(request.website.sale_product_domain()) & Domain(
            "industry_ids", "in", industry.id
        )
        products = (
            request.env["product.template"]
            .search(domain, order="website_sequence asc, name asc", limit=12)
        )
        total_products = request.env["product.template"].search_count(domain)

        # Other active industries for cross-navigation
        other_industries = (
            request.env["sre.industry"]
            .sudo()
            .search(
                [("active", "=", True), ("id", "!=", industry.id)],
                order="sequence, name",
                limit=6,
            )
        )

        return request.render(
            "mechanic_workshop.sre_industry_detail",
            {
                "industry": industry,
                "products": products,
                "total_products": total_products,
                "other_industries": other_industries,
            },
        )

    # -------------------------------------------------------------------------
    # Application Routes
    # -------------------------------------------------------------------------

    @http.route(
        ["/sre/application", "/sre/application/"],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def application_index(self, **kw: object) -> http.Response:
        """Render the directory of all published SRE applications."""
        del kw
        applications = (
            request.env["sre.application"]
            .sudo()
            .search([("active", "=", True)], order="sequence, name")
        )
        return request.render(
            "mechanic_workshop.sre_application_index",
            {
                "applications": applications,
            },
        )

    @http.route(
        "/sre/application/<string:application_slug>",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def application_detail(
        self, application_slug: str, **kw: object
    ) -> http.Response:
        """Render the specialized landing page for a system application."""
        del kw
        application = (
            request.env["sre.application"]
            .sudo()
            .search(
                [("slug", "=", application_slug), ("active", "=", True)],
                limit=1,
            )
        )
        if not application:
            return request.not_found()

        # Fetch published products mapped to this application
        domain = Domain(request.website.sale_product_domain()) & Domain(
            "application_ids", "in", application.id
        )
        products = (
            request.env["product.template"]
            .search(domain, order="website_sequence asc, name asc", limit=12)
        )
        total_products = request.env["product.template"].search_count(domain)

        # Other active applications for cross-navigation
        other_applications = (
            request.env["sre.application"]
            .sudo()
            .search(
                [("active", "=", True), ("id", "!=", application.id)],
                order="sequence, name",
                limit=6,
            )
        )

        return request.render(
            "mechanic_workshop.sre_application_detail",
            {
                "application": application,
                "products": products,
                "total_products": total_products,
                "other_applications": other_applications,
            },
        )
