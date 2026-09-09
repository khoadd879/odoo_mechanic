"""SRE Attribute Profile — per-family technical filter scope.

Brief §07 enumerates different filter sets for Valve, Pump and HVAC
Instrument and explicitly forbids one shared filter for the whole
site (§22 #5). We implement that by mapping a profile to a subset of
native ``product.attribute`` rows, then the category page only renders
the attributes declared in the profile of the active family.

Mapping per §21: ATTRIBUTE_PROFILES → Odoo Attributes / Values
"""

from __future__ import annotations

from odoo import api, fields, models


class SreAttributeProfile(models.Model):
    _name = "sre.attribute.profile"
    _description = "SRE Attribute Profile (per-family filter set)"
    _order = "name"

    name = fields.Char(required=True, translate=True, index="trigram")
    note = fields.Text(help="Internal note; not exposed on website.")
    line_ids = fields.One2many(
        "sre.attribute.profile.attribute",
        "profile_id",
        copy=True,
        string="Attributes",
    )
    family_ids = fields.One2many(
        "sre.product.family",
        "attribute_profile_id",
        string="Used by families",
    )
    family_count = fields.Integer(
        compute="_compute_family_count",
        string="Families using this profile",
    )

    def _compute_family_count(self) -> None:
        for profile in self:
            profile.family_count = len(profile.family_ids)

    @api.onchange("name")
    def _onchange_name(self) -> None:
        if self.name and not self.note:
            self.note = False


class SreAttributeProfileAttribute(models.Model):
    _name = "sre.attribute.profile.attribute"
    _description = "Attribute in a profile"
    _order = "sequence, id"

    profile_id = fields.Many2one(
        "sre.attribute.profile",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    attribute_id = fields.Many2one(
        "product.attribute",
        required=True,
        ondelete="restrict",
        help=(
            "Native Odoo product.attribute. Its values are rendered "
            "as facets on the category page."
        ),
    )
    is_filter_shown = fields.Boolean(
        default=True,
        help="If False, attribute is in the profile but hidden from facets.",
    )
    value_ids = fields.Many2many(
        "product.attribute.value",
        relation="sre_attribute_profile_value_rel",
        column1="line_id",
        column2="value_id",
        string="Allowed values",
        help=(
            "Optional whitelist of values shown for this attribute. "
            "Leave empty to show all values used by products in scope."
        ),
    )
    _attribute_unique = models.Constraint(
        "UNIQUE(profile_id, attribute_id)",
        "Attribute may appear at most once per profile.",
    )
