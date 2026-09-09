"""SRE Industry and Application taxonomies.

Brief §14 and §15 declare Industry and Application as taxonomies
*independent* of Product Category. A product may serve many industries
and many applications; the same product must not be duplicated per
industry/application (§22 #8).

Landing pages for these taxonomies belong to Sprint 3; the models and
M2M relations are introduced now so the search and category page can
include them as facets later without schema migration.
"""

from __future__ import annotations

from odoo import api, fields, models


class SreIndustry(models.Model):
    _name = "sre.industry"
    _description = "SRE Industry (taxonomy, independent of product category)"
    _order = "sequence, name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10, index=True)
    description = fields.Html(
        sanitize_attributes=False,
        help="Public landing page copy. No supplier or pricing info.",
    )
    active = fields.Boolean(default=True)
    product_ids = fields.Many2many(
        "product.template",
        "sre_industry_product_rel",
        "industry_id",
        "product_tmpl_id",
        string="Products",
    )
    product_count = fields.Integer(
        compute="_compute_product_count",
        string="Published products",
    )

    _slug_unique = models.Constraint(
        "UNIQUE(slug)",
        "Industry slug must be unique.",
    )

    def _normalize_slug(self, slug: str | None) -> str:
        return (slug or "").strip().lower().replace(" ", "-")

    @api.model_create_multi
    def create(self, vals_list: list[dict]) -> models.Model:
        for vals in vals_list:
            if vals.get("slug"):
                vals["slug"] = self._normalize_slug(vals["slug"])
        return super().create(vals_list)

    def write(self, vals: dict) -> bool:
        if vals.get("slug"):
            vals["slug"] = self._normalize_slug(vals["slug"])
        return super().write(vals)

    def _compute_product_count(self) -> None:
        for ind in self:
            ind.product_count = self.env["product.template"].search_count([
                ("industry_ids", "in", ind.id),
                ("is_published", "=", True),
            ])


class SreApplication(models.Model):
    _name = "sre.application"
    _description = "SRE Application (taxonomy, independent of product category)"
    _order = "sequence, name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10, index=True)
    description = fields.Html(
        sanitize_attributes=False,
        help="Public landing page copy. No supplier or pricing info.",
    )
    active = fields.Boolean(default=True)
    product_ids = fields.Many2many(
        "product.template",
        "sre_application_product_rel",
        "application_id",
        "product_tmpl_id",
        string="Products",
    )
    product_count = fields.Integer(
        compute="_compute_product_count",
        string="Published products",
    )

    _slug_unique = models.Constraint(
        "UNIQUE(slug)",
        "Application slug must be unique.",
    )

    def _normalize_slug(self, slug: str | None) -> str:
        return (slug or "").strip().lower().replace(" ", "-")

    @api.model_create_multi
    def create(self, vals_list: list[dict]) -> models.Model:
        for vals in vals_list:
            if vals.get("slug"):
                vals["slug"] = self._normalize_slug(vals["slug"])
        return super().create(vals_list)

    def write(self, vals: dict) -> bool:
        if vals.get("slug"):
            vals["slug"] = self._normalize_slug(vals["slug"])
        return super().write(vals)

    def _compute_product_count(self) -> None:
        for app in self:
            app.product_count = self.env["product.template"].search_count([
                ("application_ids", "in", app.id),
                ("is_published", "=", True),
            ])
