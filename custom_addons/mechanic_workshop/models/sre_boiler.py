"""SRE Boiler Part Discovery Models (Brief §11 — P0).

Provides a structured 4-step discovery engine hierarchy:
Boiler Manufacturer -> Boiler Type -> Boiler Model -> Subsystem/Component -> Verified Replacement Part.
"""

from __future__ import annotations

from odoo import api, fields, models


class SreBoilerManufacturer(models.Model):
    """Boiler equipment manufacturer / make."""

    _name = "sre.boiler.manufacturer"
    _description = "Boiler Manufacturer (Make)"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(required=True, index=True)
    country_name = fields.Char(string="Origin / Headquarters", translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    model_ids = fields.One2many(
        "sre.boiler.model",
        "manufacturer_id",
        string="Boiler Models",
    )
    model_count = fields.Integer(
        compute="_compute_counts",
        string="Models Count",
    )
    part_count = fields.Integer(
        compute="_compute_counts",
        string="Verified Parts Count",
    )

    _check_slug_unique = models.Constraint(
        "unique (slug)",
        "Boiler manufacturer slug must be unique.",
    )

    @api.depends("model_ids", "model_ids.mapping_ids")
    def _compute_counts(self) -> None:
        for record in self:
            record.model_count = len(record.model_ids)
            parts = record.model_ids.mapped("mapping_ids.product_tmpl_id")
            record.part_count = len(parts)


class SreBoilerType(models.Model):
    """Boiler technology classification (Watertube, Firetube, etc.)."""

    _name = "sre.boiler.type"
    _description = "Boiler Type / Architecture"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(required=True, index=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    model_ids = fields.One2many(
        "sre.boiler.model",
        "boiler_type_id",
        string="Boiler Models",
    )

    _check_slug_unique = models.Constraint(
        "unique (slug)",
        "Boiler type slug must be unique.",
    )


class SreBoilerSubsystem(models.Model):
    """Boiler functional subsystem / component group per Brief §11."""

    _name = "sre.boiler.subsystem"
    _description = "Boiler Subsystem / Component Group"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(required=True, index=True)
    icon = fields.Char(default="fa-cogs", help="FontAwesome icon class")
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _check_slug_unique = models.Constraint(
        "unique (slug)",
        "Boiler subsystem slug must be unique.",
    )


class SreBoilerModel(models.Model):
    """Specific boiler series or model."""

    _name = "sre.boiler.model"
    _description = "Boiler Series / Model"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True, index="trigram")
    slug = fields.Char(required=True, index=True)
    manufacturer_id = fields.Many2one(
        "sre.boiler.manufacturer",
        required=True,
        ondelete="cascade",
        index=True,
        string="Manufacturer",
    )
    boiler_type_id = fields.Many2one(
        "sre.boiler.type",
        required=True,
        ondelete="restrict",
        index=True,
        string="Boiler Type",
    )
    steam_capacity_kg_h = fields.Float(
        string="Steam Capacity (kg/h)",
        help="Nominal steam output in kilograms per hour.",
    )
    design_pressure_bar = fields.Float(
        string="Design Pressure (bar)",
        help="Maximum design pressure in bar.",
    )
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    mapping_ids = fields.One2many(
        "sre.boiler.part.mapping",
        "boiler_model_id",
        string="Mapped Parts",
    )
    part_count = fields.Integer(
        compute="_compute_part_count",
        string="Parts Count",
    )

    _check_slug_unique = models.Constraint(
        "unique (slug)",
        "Boiler model slug must be unique.",
    )

    @api.depends("mapping_ids")
    def _compute_part_count(self) -> None:
        for record in self:
            record.part_count = len(record.mapping_ids.mapped("product_tmpl_id"))


class SreBoilerPartMapping(models.Model):
    """Verified part-to-boiler compatibility mapping."""

    _name = "sre.boiler.part.mapping"
    _description = "Boiler Part Compatibility Mapping"
    _order = "sequence, id"

    boiler_model_id = fields.Many2one(
        "sre.boiler.model",
        required=True,
        ondelete="cascade",
        index=True,
        string="Boiler Model",
    )
    subsystem_id = fields.Many2one(
        "sre.boiler.subsystem",
        required=True,
        ondelete="restrict",
        index=True,
        string="Subsystem",
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
        index=True,
        string="Replacement Part (Product)",
    )
    position_ref = fields.Char(
        string="Position / Role",
        translate=True,
        help="Exact installation location or duty on the boiler.",
    )
    is_critical_spare = fields.Boolean(
        string="Critical Spare Part",
        default=False,
        help="Indicates essential spare parts needed to prevent unscheduled boiler outages.",
    )
    notes = fields.Text(
        string="Engineering Notes",
        translate=True,
        help="Specific replacement instructions or fitting notes.",
    )
    sequence = fields.Integer(default=10)
