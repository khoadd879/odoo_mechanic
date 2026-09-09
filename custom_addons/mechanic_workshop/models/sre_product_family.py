"""SRE Product Family — middle layer between Pillar and Product.

PIM V2 README documents the chain::

    PRODUCT → CATEGORY → PRODUCT FAMILY → ATTRIBUTE PROFILE

A Family groups products that share a technical filter set (brief
§07). Each family belongs to exactly one Pillar (brief §04 navigation
groups) and carries one Attribute Profile (brief §07 filter scope).

Distinguishing Pillar from Family matters because:
  * Brief §07 enumerates filters for *families* (Valve, Pump, HVAC
    Instrument), not for pillars.
  * One Pillar can contain many Families — e.g. the "HVAC & Building"
    pillar may contain "HVAC Instrument", "AHU Component" and
    "Building Controller" families, each with its own filter profile.
  * §22 #7 forbids hard-coding the category structure into the
    frontend; both Pillar and Family are data-driven.
"""

from __future__ import annotations

from odoo import api, fields, models


class SreProductFamily(models.Model):
    _name = "sre.product.family"
    _description = "SRE Product Family (filter scope under a Pillar)"
    _order = "pillar_id, sequence, name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(
        required=True,
        index=True,
        help="URL slug, e.g. 'valve'. Lowercase, hyphenated.",
    )
    sequence = fields.Integer(default=10, index=True)
    pillar_id = fields.Many2one(
        "sre.navigation.pillar",
        string="Pillar",
        ondelete="set null",
        index=True,
        help=(
            "Navigation pillar that groups this family in the site "
            "top-nav and the pillar landing page. Brief §04."
        ),
    )
    description = fields.Html(
        help=(
            "Public-facing description for the family landing page. "
            "Plain technical text; do not embed supplier or pricing."
        ),
    )
    attribute_profile_id = fields.Many2one(
        "sre.attribute.profile",
        ondelete="set null",
        help=(
            "Attribute profile that scopes the technical filters "
            "shown on this family's category page. Brief §07 requires "
            "filters to be per-family; leave empty to render no facet."
        ),
    )
    is_published = fields.Boolean(default=True, index=True)
    active = fields.Boolean(default=True)
    product_count = fields.Integer(
        compute="_compute_product_count",
        help="Number of published products in this family.",
    )

    _slug_unique = models.Constraint(
        "UNIQUE(slug)",
        "Family slug must be unique.",
    )

    @api.depends("name")
    def _compute_product_count(self) -> None:
        Product = self.env["product.template"]
        for family in self:
            family.product_count = Product.search_count([
                ("family_id", "=", family.id),
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
