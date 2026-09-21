from __future__ import annotations

import math
from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import SQL


class SreRfq(models.Model):
    _name = "sre.rfq"
    _description = "Customer RFQ"
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(required=True, default=lambda self: _("New"), copy=False, readonly=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    website_id = fields.Many2one("website", readonly=True)
    submission_key = fields.Char(copy=False, readonly=True, groups="base.group_system")
    _submission_unique = models.Constraint("UNIQUE(submission_key)", "Request already submitted.")
    contact_name = fields.Char(required=True)
    company_name = fields.Char(required=True)
    email = fields.Char(required=True)
    phone = fields.Char()
    project_name = fields.Char()
    project_location = fields.Char()
    required_delivery_date = fields.Date()
    notes = fields.Text()
    nameplate_image = fields.Binary("Nameplate Photo / Spec Document", attachment=True)
    nameplate_filename = fields.Char("Nameplate Filename")
    is_unknown_part = fields.Boolean("Unknown Part Identification Request", default=False)
    equipment_make_model = fields.Char("Equipment Make / Series / Model")
    operating_medium = fields.Selection([
        ("saturated_steam", "Saturated Steam / Hơi bão hòa"),
        ("superheated_steam", "Superheated Steam / Hơi quá nhiệt"),
        ("condensate", "Condensate / Nước ngưng"),
        ("feedwater", "Feedwater / Nước cấp lò hơi"),
        ("thermal_oil", "Thermal Oil / Dầu truyền nhiệt"),
        ("compressed_air", "Compressed Air / Khí nén"),
        ("lpg_gas", "LPG / Gas / Khí đốt"),
        ("other", "Other Media / Môi chất khác"),
    ], string="Operating Fluid / Medium")
    operating_pressure = fields.Float("Operating Pressure (bar)", digits=(6, 2))
    operating_temperature = fields.Float("Operating Temperature (°C)", digits=(6, 1))
    connection_type = fields.Char("Connection Type & Size (Flange/Thread/DN)")
    partner_id = fields.Many2one("res.partner", string="Verified customer", check_company=True)
    state = fields.Selection([("submitted", "Submitted"), ("quoted", "Quotation created")], default="submitted", required=True, readonly=True)
    line_ids = fields.One2many("sre.rfq.line", "rfq_id", copy=True)
    lead_id = fields.Many2one("crm.lead", readonly=True, copy=False, check_company=True)
    order_id = fields.Many2one("sale.order", readonly=True, copy=False, check_company=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self.env["ir.sequence"].next_by_code("sre.rfq") or _("New")
        return super().create(vals_list)

    def _create_opportunity(self):
        self.ensure_one()
        if not self.lead_id:
            lead_name = f"{self.name} — {self.company_name}"
            if self.is_unknown_part:
                lead_name = f"[UNKNOWN PART IDENTIFICATION] {self.name} — {self.company_name}"

            desc_parts = []
            if self.project_name:
                desc_parts.append(f"Project: {self.project_name}")
            if self.project_location:
                desc_parts.append(f"Location: {self.project_location}")
            if self.is_unknown_part:
                desc_parts.append("=== UNKNOWN PART IDENTIFICATION SPECIFICATIONS ===")
                if self.equipment_make_model:
                    desc_parts.append(f"• Equipment Make/Model: {self.equipment_make_model}")
                if self.operating_medium:
                    desc_parts.append(f"• Operating Fluid: {dict(self._fields['operating_medium'].selection).get(self.operating_medium, self.operating_medium)}")
                if self.operating_pressure:
                    desc_parts.append(f"• Operating Pressure: {self.operating_pressure} bar")
                if self.operating_temperature:
                    desc_parts.append(f"• Operating Temperature: {self.operating_temperature} °C")
                if self.connection_type:
                    desc_parts.append(f"• Connection / Port Size: {self.connection_type}")
            if self.notes:
                desc_parts.append(f"\nCustomer Notes:\n{self.notes}")

            lead = self.env["crm.lead"].create({
                "name": lead_name,
                "type": "opportunity",
                "contact_name": self.contact_name,
                "partner_name": self.company_name,
                "email_from": self.email,
                "phone": self.phone,
                "company_id": self.company_id.id,
                "description": "\n".join(desc_parts) if desc_parts else False,
                "priority": "3" if self.is_unknown_part else "1",
                "sre_rfq_id": self.id,
            })
            self.lead_id = lead
            if self.nameplate_image:
                self.env["ir.attachment"].create({
                    "name": self.nameplate_filename or f"{self.name}-nameplate",
                    "datas": self.nameplate_image,
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                })

    def action_create_quotation(self):
        self.ensure_one()
        self.check_access("write")
        # Serialize concurrent button clicks; never create duplicate quotations.
        self.env.cr.execute(SQL("SELECT id FROM sre_rfq WHERE id = %s FOR UPDATE", self.id))
        self.invalidate_recordset(["order_id"])
        if not self.order_id:
            if not self.partner_id or not self.line_ids:
                raise UserError(_("Select a verified customer and add at least one product."))
            self._create_opportunity()
            order = self.env["sale.order"].with_company(self.company_id).create({
                "partner_id": self.partner_id.id, "company_id": self.company_id.id,
                "origin": self.name, "opportunity_id": self.lead_id.id,
                "sre_rfq_id": self.id,
                "order_line": [Command.create({
                    "product_id": line.product_id.id,
                    "product_uom_qty": line.quantity,
                    "product_uom_id": line.uom_id.id,
                }) for line in self.line_ids],
            })
            self.write({"order_id": order.id, "state": "quoted"})
        return {"type": "ir.actions.act_window", "res_model": "sale.order",
                "res_id": self.order_id.id, "view_mode": "form", "target": "current"}


class SreRfqLine(models.Model):
    _name = "sre.rfq.line"
    _description = "Customer RFQ Line"
    _check_company_auto = True

    rfq_id = fields.Many2one("sre.rfq", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="rfq_id.company_id", store=True)
    product_id = fields.Many2one("product.product", required=True, check_company=True)
    quantity = fields.Float(required=True, default=1, digits="Product Unit")
    uom_id = fields.Many2one(related="product_id.uom_id", store=True)

    @api.model
    def _validate_quantity_value(self, value):
        try:
            quantity = float(value)
        except (ValueError, TypeError):
            raise ValidationError(_("Invalid quantity.")) from None
        if not math.isfinite(quantity) or not 0 < quantity <= 1000000:
            raise ValidationError(_("Quantity must be greater than zero and at most 1,000,000."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_quantity_value(vals.get("quantity", 1))
        return super().create(vals_list)

    def write(self, vals):
        if "quantity" in vals:
            self._validate_quantity_value(vals["quantity"])
        return super().write(vals)

    @api.constrains("quantity")
    def _check_quantity(self):
        for line in self:
            if not math.isfinite(line.quantity) or not 0 < line.quantity <= 1000000:
                raise ValidationError(_("Quantity must be greater than zero and at most 1,000,000."))


class CrmLead(models.Model):
    _inherit = "crm.lead"
    sre_rfq_id = fields.Many2one("sre.rfq", readonly=True, copy=False, check_company=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    sre_rfq_id = fields.Many2one("sre.rfq", readonly=True, copy=False, check_company=True)
