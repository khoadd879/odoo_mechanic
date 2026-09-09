"""SRE Navigation Pillar — top-level business category for the site.

Brief §04 fixes 8 business pillars that drive the public navigation:
  1. HVAC & Building
  2. Boiler & Thermal
  3. Pumps
  4. Valves
  5. Heat Exchangers
  6. Instrumentation
  7. Controls & Automation
  8. Industrial Spare Parts

A Pillar is a *grouping* for navigation and for the "Shop by …
" hero blocks. It is NOT the same as Product Family. One pillar
contains many families. For example:

  Pillar "Pumps"     → families [Centrifugal Pump, Submersible Pump, …]
  Pillar "Valves"    → families [Control Valve, Safety Valve, …]
  Pillar "HVAC & Building" → families [HVAC Instrument, AHU Component, …]

Brief §07's "Valve / Pump / HVAC Instrument" labels are families
(family carries an attribute profile); the §04 list are pillars.
The PIM V2 README documents the chain

  PRODUCT → CATEGORY → PRODUCT FAMILY → ATTRIBUTE PROFILE

so a Pillar sits *above* Family in the navigation hierarchy and is
not the same model. We introduce a dedicated ``sre.navigation.pillar``
model to keep navigation data-driven (§22 #7 forbids hard-coding
the list) and the family model stays clean.
"""

from __future__ import annotations

from odoo import api, fields, models


class SreNavigationPillar(models.Model):
    _name = "sre.navigation.pillar"
    _description = "SRE Navigation Pillar (top-level site section)"
    _order = "sequence, name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(
        required=True,
        index=True,
        help="URL slug, e.g. 'valves'. Lowercase, hyphenated.",
    )
    sequence = fields.Integer(default=10, index=True)
    short_label = fields.Char(
        translate=True,
        help="Optional shorter label for the top nav (e.g. 'HVAC').",
    )
    description = fields.Html(
        help="Public copy for the pillar landing page.",
    )
    icon = fields.Char(
        help=(
            "Optional icon identifier (Font Awesome class or "
            "Bootstrap icon name). Leave empty to render plain text."
        ),
    )
    is_published = fields.Boolean(default=True, index=True)
    active = fields.Boolean(default=True)
    family_ids = fields.One2many(
        "sre.product.family",
        "pillar_id",
        string="Families in this pillar",
    )
    family_count = fields.Integer(
        compute="_compute_family_count",
        string="Families",
    )
    product_count = fields.Integer(
        compute="_compute_product_count",
        string="Published products",
    )

    _slug_unique = models.Constraint(
        "UNIQUE(slug)",
        "Pillar slug must be unique.",
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

    @api.depends("family_ids")
    def _compute_family_count(self) -> None:
        for pillar in self:
            pillar.family_count = len(pillar.family_ids)

    @api.depends("family_ids")
    def _compute_product_count(self) -> None:
        Product = self.env["product.template"]
        for pillar in self:
            family_ids = pillar.family_ids.ids
            if not family_ids:
                pillar.product_count = 0
                continue
            pillar.product_count = Product.search_count([
                ("family_id", "in", family_ids),
                ("is_published", "=", True),
            ])
