"""SRE Cross Reference Engine (Brief §12 — P0).

Allows technical buyers to look up competitor or OEM part numbers
(Spirax Sarco, TLV, Armstrong, Yoshitake, Forbes Marshall, etc.)
and map them to verified SRE replacement products with defined equivalence grades.
"""

from __future__ import annotations

from odoo import api, fields, models


class SreProductCrossReference(models.Model):
    """Mapping from external OEM / competitor part number to SRE product."""

    _name = "sre.product.cross.reference"
    _description = "Product Cross Reference"
    _order = "source_brand, source_part_number"

    source_part_number = fields.Char(
        string="Competitor / OEM Part Number",
        required=True,
        index="trigram",
        help="Part number or catalog code of competitor or original equipment manufacturer.",
    )
    source_brand = fields.Char(
        string="Brand / Manufacturer",
        required=True,
        index=True,
        help="Competitor or OEM brand (e.g. Spirax Sarco, TLV, Armstrong, Yoshitake).",
    )
    source_specs = fields.Char(
        string="Original Specifications",
        help="Summary specs of original part (e.g. DN25 PN16 Thermodynamic Steam Trap).",
    )
    target_product_id = fields.Many2one(
        "product.template",
        string="SRE Replacement Product",
        required=True,
        ondelete="cascade",
        index=True,
    )
    replacement_type = fields.Selection(
        [
            ("direct", "Direct Replacement (100% Fit & Function)"),
            ("drop_in", "Drop-in Alternative (Functional Equivalent)"),
            ("obsolete", "Obsolete Replacement (Modern Upgrade)"),
        ],
        string="Equivalence Grade",
        default="direct",
        required=True,
        help="Direct = 100% dimension & spec match; Drop-in = functional equivalent; Obsolete = replaces discontinued item.",
    )
    notes = fields.Text(
        string="Engineering & Fitment Notes",
        translate=True,
        help="Important technical differences, face-to-face dimensions, or flange pattern requirements.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _check_unique_xref = models.Constraint(
        "unique (source_brand, source_part_number, target_product_id)",
        "This cross reference mapping already exists.",
    )

    @api.depends("source_brand", "source_part_number")
    def _compute_display_name(self) -> None:
        for rec in self:
            rec.display_name = f"[{rec.source_brand}] {rec.source_part_number} → {rec.target_product_id.name or ''}"
