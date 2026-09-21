"""SRE Customer Equipment Model (My Plant / Saved Equipment — Brief §18).

Allows B2B customers to register and manage machines running in their factories,
automatically linking verified compatible spare parts from Boiler Discovery & Compatibility Matrix.
"""

from __future__ import annotations

from odoo import api, fields, models, _


class SreCustomerEquipment(models.Model):
    """Customer-owned industrial machinery and equipment installed at plant."""

    _name = "sre.customer.equipment"
    _description = "Customer Plant Equipment"
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(string="Equipment Name", required=True, translate=True)
    plant_tag = fields.Char(string="Plant Tag / Asset ID", index=True, help="Internal tag used by factory engineers (e.g. BLR-01, PUMP-CW-02)")
    partner_id = fields.Many2one(
        "res.partner",
        string="Plant / Customer",
        required=True,
        default=lambda self: self.env.user.partner_id.commercial_partner_id,
        index=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    location = fields.Char(string="Location / Department", help="e.g. Boiler House, Dyeing Line 2, RO Plant")
    equipment_type = fields.Selection([
        ("boiler", "Industrial Boiler / Nồi hơi công nghiệp"),
        ("pump", "Pump / Trạm bơm công nghiệp"),
        ("valve_station", "Valve Station / Cụm van điều khiển"),
        ("heat_exchanger", "Heat Exchanger / Bộ trao đổi nhiệt"),
        ("chiller_hvac", "HVAC / Chiller / Hệ thống lạnh"),
        ("instrumentation", "Instrumentation / Cảm biến & Đo lường"),
        ("other", "Other Equipment / Thiết bị khác"),
    ], string="Equipment Type", default="boiler", required=True)

    # Optional boiler link
    boiler_manufacturer_id = fields.Many2one("sre.boiler.manufacturer", string="Boiler Make / Hãng sản xuất")
    boiler_model_id = fields.Many2one(
        "sre.boiler.model",
        string="Boiler Model / Dòng máy",
        domain="[('manufacturer_id', '=', boiler_manufacturer_id)] if boiler_manufacturer_id else []",
    )

    serial_number = fields.Char(string="Serial Number / Số chế tạo")
    commissioning_year = fields.Integer(string="Commissioning Year / Năm vận hành")
    operating_medium = fields.Selection([
        ("saturated_steam", "Saturated Steam / Hơi bão hòa"),
        ("superheated_steam", "Superheated Steam / Hơi quá nhiệt"),
        ("condensate", "Condensate / Nước ngưng"),
        ("feedwater", "Feedwater / Nước cấp lò hơi"),
        ("thermal_oil", "Thermal Oil / Dầu truyền nhiệt"),
        ("chilled_water", "Chilled Water / Nước lạnh HVAC"),
        ("compressed_air", "Compressed Air / Khí nén"),
        ("other", "Other Fluid / Môi chất khác"),
    ], string="Operating Medium")
    operating_pressure = fields.Float(string="Operating Pressure (bar)", digits=(6, 2))
    operating_temperature = fields.Float(string="Operating Temperature (°C)", digits=(6, 1))
    notes = fields.Text(string="Maintenance & Engineering Notes")

    # Spare Parts
    saved_part_ids = fields.Many2many(
        "product.template",
        "sre_customer_equipment_saved_parts_rel",
        "equipment_id",
        "product_tmpl_id",
        string="Pinned Spare Parts",
    )
    compatible_part_ids = fields.Many2many(
        "product.template",
        compute="_compute_compatible_parts",
        string="Verified Compatible Spares",
    )
    compatible_part_count = fields.Integer(
        compute="_compute_compatible_parts",
        string="Compatible Parts Count",
    )
    critical_part_count = fields.Integer(
        compute="_compute_compatible_parts",
        string="Critical Spares Count",
    )

    @api.depends("boiler_model_id", "saved_part_ids")
    def _compute_compatible_parts(self):
        for rec in self:
            parts = rec.saved_part_ids
            critical_count = 0
            if rec.boiler_model_id:
                mappings = self.env["sre.boiler.part.mapping"].search([
                    ("boiler_model_id", "=", rec.boiler_model_id.id),
                ])
                boiler_parts = mappings.mapped("product_tmpl_id")
                critical_count = len(mappings.filtered("is_critical_spare").mapped("product_tmpl_id"))
                parts = parts | boiler_parts
            rec.compatible_part_ids = parts
            rec.compatible_part_count = len(parts)
            rec.critical_part_count = critical_count
