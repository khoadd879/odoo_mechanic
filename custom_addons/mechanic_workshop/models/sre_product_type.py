"""SRE Product Type — Level 4 subtype under a Product Family.

The taxonomy hierarchy follows:
    Pillar (Level 1) → Category (Level 2) → Product Family (Level 3) → Product Type (Level 4)

Product Type provides fine-grained structural/sub-type classification under a family
(e.g., under End Suction Pump: "Close-coupled", "Frame-mounted", "Bare shaft").
"""

from __future__ import annotations

from odoo import api, fields, models


class SreProductType(models.Model):
    _name = "sre.product.type"
    _description = "SRE Product Type (Level 4 subtype under a Family)"
    _order = "family_id, sequence, name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(
        required=True,
        index=True,
        help="URL slug, e.g. 'close-coupled'. Lowercase, hyphenated.",
    )
    sequence = fields.Integer(default=10, index=True)
    family_id = fields.Many2one(
        "sre.product.family",
        string="Product Family",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent product family (Level 3).",
    )
    category_id = fields.Many2one(
        related="family_id.category_id",
        string="Category",
        store=True,
        readonly=True,
        index=True,
    )
    pillar_id = fields.Many2one(
        related="family_id.pillar_id",
        string="Pillar",
        store=True,
        readonly=True,
        index=True,
    )
    description = fields.Text(
        help="Technical notes on this subtype.",
    )
    active = fields.Boolean(default=True)

    product_tmpl_ids = fields.One2many(
        "product.template",
        "product_type_id",
        string="Products",
    )
    product_count = fields.Integer(
        compute="_compute_product_count",
        string="Product Count",
    )

    _slug_unique = models.Constraint(
        "UNIQUE(family_id, slug)",
        "Product type slug must be unique per family.",
    )

    @api.depends("product_tmpl_ids")
    def _compute_product_count(self) -> None:
        Product = self.env["product.template"]
        for ptype in self:
            ptype.product_count = Product.search_count([
                ("product_type_id", "=", ptype.id),
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
