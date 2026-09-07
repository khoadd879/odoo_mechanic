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
            self.lead_id = self.env["crm.lead"].create({
                "name": self.name + " — " + self.company_name,
                "type": "opportunity", "contact_name": self.contact_name,
                "partner_name": self.company_name, "email_from": self.email,
                "phone": self.phone, "company_id": self.company_id.id,
                "sre_rfq_id": self.id,
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
