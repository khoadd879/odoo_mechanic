# Part of SRE Commercial Platform / Mechanic Workshop.
# Brief §16: Document Governance & Rights QA.

import os
from odoo import api, fields, models, _


class SreProductDocument(models.Model):
    _inherit = "product.document"

    document_type = fields.Selection(
        [
            ("datasheet", "Datasheet / Technical Spec"),
            ("manual", "Installation & Operation Manual"),
            ("cad_drawing", "2D/3D CAD Drawing"),
            ("certificate", "Certificate & Compliance (CO/CQ, CE)"),
            ("brochure", "Catalog & Brochure"),
        ],
        string="Document Type",
        default="datasheet",
        required=True,
        index=True,
    )

    governance_type = fields.Selection(
        [
            ("public", "Public (Direct Download)"),
            ("gated", "Gated (Business Contact Required)"),
            ("internal", "Internal Only (Engineering Staging)"),
        ],
        string="Document Governance",
        default="public",
        required=True,
        index=True,
        help="Public: anyone can download. Gated: requires B2B contact info before downloading (generates CRM lead). Internal: only visible in backend.",
    )

    cad_format = fields.Selection(
        [
            ("pdf", "PDF Document"),
            ("step", "STEP 3D Model"),
            ("dwg", "AutoCAD DWG"),
            ("dxf", "2D DXF"),
            ("zip", "ZIP Archive"),
            ("other", "Other"),
        ],
        string="File Format",
        default="pdf",
        required=True,
    )

    download_count = fields.Integer(
        string="Download Count",
        default=0,
        readonly=True,
    )

    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product Template",
        compute="_compute_product_tmpl_id",
        store=True,
        index=True,
    )

    @api.depends("res_model", "res_id")
    def _compute_product_tmpl_id(self):
        for doc in self:
            if doc.res_model == "product.template" and doc.res_id:
                doc.product_tmpl_id = doc.res_id
            else:
                doc.product_tmpl_id = False

    @api.onchange("governance_type")
    def _onchange_governance_type(self):
        for doc in self:
            if doc.governance_type == "internal":
                doc.shown_on_product_page = False
            elif doc.governance_type in ("public", "gated") and doc.res_model == "product.template":
                doc.shown_on_product_page = True

    @api.onchange("name")
    def _onchange_name_detect_format(self):
        for doc in self:
            if doc.name:
                ext = os.path.splitext(doc.name)[1].lower()
                if ext == ".pdf":
                    doc.cad_format = "pdf"
                elif ext in (".step", ".stp"):
                    doc.cad_format = "step"
                elif ext == ".dwg":
                    doc.cad_format = "dwg"
                elif ext == ".dxf":
                    doc.cad_format = "dxf"
                elif ext in (".zip", ".rar", ".7z", ".tar", ".gz"):
                    doc.cad_format = "zip"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("governance_type") == "internal":
                vals["shown_on_product_page"] = False
            elif vals.get("governance_type") in ("public", "gated") and vals.get("res_model") == "product.template":
                if "shown_on_product_page" not in vals:
                    vals["shown_on_product_page"] = True
            if "name" in vals and "cad_format" not in vals:
                ext = os.path.splitext(vals["name"])[1].lower()
                if ext == ".pdf":
                    vals["cad_format"] = "pdf"
                elif ext in (".step", ".stp"):
                    vals["cad_format"] = "step"
                elif ext == ".dwg":
                    vals["cad_format"] = "dwg"
                elif ext == ".dxf":
                    vals["cad_format"] = "dxf"
                elif ext in (".zip", ".rar", ".7z", ".tar", ".gz"):
                    vals["cad_format"] = "zip"
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("governance_type") == "internal":
            vals["shown_on_product_page"] = False
        return super().write(vals)

    def action_register_download(self):
        """Atomically increment download count."""
        for doc in self:
            doc.sudo().download_count += 1
