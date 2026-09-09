"""SRE OEM Part Number — scaffold for Cross Reference engine (Sprint 2).

Brief §05 lists OEM Part Number as a P0 search target. The current
Sprint 1 only needs the row to exist so search can match it as
``product.sre_oem_pn_ids.oem_part_number``. The full cross-reference
graph (Alternative, Replacement, Accessory, Related) is a Sprint 2
deliverable per §24.

Privacy: this internal model has no public ACL because its manufacturer,
source classification and notes are staff data. Website users can only
read the stored ``product.template.sre_public_oem_part_numbers`` text
projection; supplier, cost, sourcing and note fields stay private
(§17, §22 #9).
"""

from __future__ import annotations

from odoo import api, fields, models


class SreOemPn(models.Model):
    _name = "sre.oem.pn"
    _description = "SRE OEM Part Number"
    _order = "product_tmpl_id, sequence, id"
    _rec_name = "oem_part_number"

    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    oem_part_number = fields.Char(required=True, index=True)
    manufacturer_id = fields.Many2one(
        "res.partner",
        string="Manufacturer",
        domain=[],
        help=(
            "Legal entity that issued the OEM part number. May be "
            "the same as or different from the product's Brand. "
            "Internal supply status is not exposed on the website."
        ),
    )
    source = fields.Selection(
        [
            ("oem", "OEM part number"),
            ("cross_ref", "Cross reference"),
            ("replacement", "Replacement"),
            ("alternative", "Alternative"),
        ],
        default="oem",
        required=True,
        help=(
            "Sprint 2 will use this field to build the cross-reference "
            "graph on the product page. Sprint 1 only uses it to "
            "control which OEM PN rows are surfaced in search."
        ),
    )
    notes = fields.Char(help="Internal note, not shown on website.")
    active = fields.Boolean(default=True)

    _part_number_unique = models.Constraint(
        "UNIQUE(product_tmpl_id, oem_part_number, manufacturer_id)",
        "Duplicate OEM part number for the same product and manufacturer.",
    )

    @api.model_create_multi
    def create(self, vals_list: list[dict]) -> models.Model:
        for vals in vals_list:
            if vals.get("oem_part_number"):
                vals["oem_part_number"] = vals["oem_part_number"].strip()
        return super().create(vals_list)

    def write(self, vals: dict) -> bool:
        if vals.get("oem_part_number"):
            vals["oem_part_number"] = vals["oem_part_number"].strip()
        return super().write(vals)
