"""SRE Product Category — Level 2 middle layer between Pillar and Product Family.

The taxonomy hierarchy follows:
    Pillar (Level 1) → Category (Level 2) → Product Family (Level 3) → Product Type (Level 4)

Categories group related families within a business pillar (e.g. Pillar "Pumps" contains
Categories like "Centrifugal Pumps", "Positive Displacement Pumps").
"""

from __future__ import annotations

from odoo import api, fields, models


class SreProductCategory(models.Model):
    _name = "sre.product.category"
    _description = "SRE Product Category (Level 2 under a Pillar)"
    _order = "pillar_id, sequence, name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(
        required=True,
        index=True,
        help="URL slug, e.g. 'centrifugal-pumps'. Lowercase, hyphenated.",
    )
    sequence = fields.Integer(default=10, index=True)
    pillar_id = fields.Many2one(
        "sre.navigation.pillar",
        string="Pillar",
        ondelete="set null",
        index=True,
        help="Parent navigation pillar (Level 1) that groups this category.",
    )
    description = fields.Html(
        help="Public-facing technical description for the category landing page.",
    )
    is_published = fields.Boolean(default=True, index=True)
    active = fields.Boolean(default=True)

    family_ids = fields.One2many(
        "sre.product.family",
        "category_id",
        string="Product Families",
    )
    family_count = fields.Integer(
        compute="_compute_family_count",
        string="Families Count",
    )
    product_count = fields.Integer(
        compute="_compute_product_count",
        string="Published Products",
    )

    _slug_unique = models.Constraint(
        "UNIQUE(slug)",
        "Category slug must be unique.",
    )

    @api.depends("family_ids")
    def _compute_family_count(self) -> None:
        for cat in self:
            cat.family_count = len(cat.family_ids)

    @api.depends("family_ids")
    def _compute_product_count(self) -> None:
        Product = self.env["product.template"]
        for cat in self:
            cat.product_count = Product.search_count([
                ("family_id.category_id", "=", cat.id),
                ("is_published", "=", True),
            ])

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
