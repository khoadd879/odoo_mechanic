"""SRE B2B Customer Portal Controller (Brief §18 & §24 — Sprint 4).

Extends Odoo's CustomerPortal to provide:
1. RFQ History & Detail (/my/rfqs, /my/rfqs/<id>)
2. 1-Click Re-order from RFQ or Sales Order (/my/rfqs/reorder/<id>, /my/orders/reorder/<id>)
3. My Plant / Saved Equipment Management (/my/plant, /my/plant/<id>, /my/plant/new)
4. Add Verified Compatible Spares to RFQ
"""

from __future__ import annotations

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from werkzeug.exceptions import NotFound, Forbidden


class SreCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if not request.env.user._is_public():
            if "rfq_count" in counters:
                domain = ["|", ("partner_id", "=", partner.id), ("email", "=", partner.email)]
                values["rfq_count"] = request.env["sre.rfq"].sudo().search_count(domain)
            if "equipment_count" in counters:
                comm_partner = partner.commercial_partner_id
                values["equipment_count"] = request.env["sre.customer.equipment"].sudo().search_count([
                    ("partner_id", "=", comm_partner.id)
                ])
        return values

    # -------------------------------------------------------------------------
    # RFQ History & Detail
    # -------------------------------------------------------------------------

    @http.route(["/my/rfqs", "/my/rfqs/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_rfqs(self, page=1, sortby=None, **kw):
        partner = request.env.user.partner_id
        Rfq = request.env["sre.rfq"].sudo()

        domain = ["|", ("partner_id", "=", partner.id), ("email", "=", partner.email)]
        rfq_count = Rfq.search_count(domain)

        pager = portal_pager(
            url="/my/rfqs",
            total=rfq_count,
            page=page,
            step=10,
        )
        rfqs = Rfq.search(domain, order="id desc", limit=10, offset=pager["offset"])

        return request.render("mechanic_workshop.sre_portal_my_rfqs", {
            "rfqs": rfqs,
            "page_name": "rfq",
            "pager": pager,
            "default_url": "/my/rfqs",
        })

    @http.route("/my/rfqs/<int:rfq_id>", type="http", auth="user", website=True)
    def portal_my_rfq_detail(self, rfq_id=None, **kw):
        partner = request.env.user.partner_id
        rfq = request.env["sre.rfq"].sudo().browse(rfq_id)
        if not rfq.exists() or (rfq.partner_id.id != partner.id and rfq.email != partner.email):
            raise NotFound()

        return request.render("mechanic_workshop.sre_portal_rfq_page", {
            "rfq": rfq,
            "page_name": "rfq",
        })

    # -------------------------------------------------------------------------
    # 1-Click Re-order
    # -------------------------------------------------------------------------

    @http.route("/my/rfqs/reorder/<int:rfq_id>", type="http", auth="user", website=True, methods=["POST", "GET"])
    def portal_reorder_rfq(self, rfq_id=None, **kw):
        partner = request.env.user.partner_id
        rfq = request.env["sre.rfq"].sudo().browse(rfq_id)
        if not rfq.exists() or (rfq.partner_id.id != partner.id and rfq.email != partner.email):
            raise NotFound()

        basket_key = "sre_rfq_basket_%s" % request.website.id
        basket = request.session.get(basket_key, {})

        for line in rfq.line_ids:
            if line.product_id:
                pid_str = str(line.product_id.id)
                basket[pid_str] = basket.get(pid_str, 0) + line.quantity

        request.session[basket_key] = basket
        return request.redirect("/rfq?reorder=1")

    @http.route("/my/orders/reorder/<int:order_id>", type="http", auth="user", website=True, methods=["POST", "GET"])
    def portal_reorder_sale_order(self, order_id=None, **kw):
        partner = request.env.user.partner_id
        order = request.env["sale.order"].sudo().browse(order_id)
        if not order.exists() or order.partner_id.commercial_partner_id.id != partner.commercial_partner_id.id:
            raise NotFound()

        basket_key = "sre_rfq_basket_%s" % request.website.id
        basket = request.session.get(basket_key, {})

        for line in order.order_line:
            if line.product_id and line.product_id.sale_ok:
                pid_str = str(line.product_id.id)
                basket[pid_str] = basket.get(pid_str, 0) + line.product_uom_qty

        request.session[basket_key] = basket
        return request.redirect("/rfq?reorder=1")

    # -------------------------------------------------------------------------
    # My Plant / Saved Equipment
    # -------------------------------------------------------------------------

    @http.route(["/my/plant", "/my/plant/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_plant(self, page=1, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        Equipment = request.env["sre.customer.equipment"].sudo()

        domain = [("partner_id", "=", partner.id)]
        equipment_count = Equipment.search_count(domain)

        pager = portal_pager(
            url="/my/plant",
            total=equipment_count,
            page=page,
            step=12,
        )
        equipments = Equipment.search(domain, order="id desc", limit=12, offset=pager["offset"])

        return request.render("mechanic_workshop.sre_portal_my_plant", {
            "equipments": equipments,
            "page_name": "plant",
            "pager": pager,
            "default_url": "/my/plant",
        })

    @http.route("/my/plant/<int:equipment_id>", type="http", auth="user", website=True)
    def portal_my_equipment_detail(self, equipment_id=None, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        equipment = request.env["sre.customer.equipment"].sudo().browse(equipment_id)
        if not equipment.exists() or equipment.partner_id.id != partner.id:
            raise NotFound()

        return request.render("mechanic_workshop.sre_portal_equipment_page", {
            "equipment": equipment,
            "page_name": "plant",
        })

    @http.route("/my/plant/new", type="http", auth="user", website=True)
    def portal_my_equipment_new(self, **kw):
        makes = request.env["sre.boiler.manufacturer"].sudo().search([("active", "=", True)])
        models = request.env["sre.boiler.model"].sudo().search([("active", "=", True)])
        return request.render("mechanic_workshop.sre_portal_equipment_form", {
            "page_name": "plant",
            "makes": makes,
            "models": models,
        })

    @http.route("/my/plant/submit", type="http", auth="user", website=True, methods=["POST"])
    def portal_my_equipment_submit(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        name = post.get("name")
        if not name:
            return request.redirect("/my/plant/new?error=name_required")

        vals = {
            "name": name,
            "plant_tag": post.get("plant_tag"),
            "partner_id": partner.id,
            "location": post.get("location"),
            "equipment_type": post.get("equipment_type", "boiler"),
            "serial_number": post.get("serial_number"),
            "commissioning_year": int(post.get("commissioning_year")) if post.get("commissioning_year") and post.get("commissioning_year").isdigit() else False,
            "operating_medium": post.get("operating_medium") or False,
            "operating_pressure": float(post.get("operating_pressure")) if post.get("operating_pressure") else 0.0,
            "operating_temperature": float(post.get("operating_temperature")) if post.get("operating_temperature") else 0.0,
            "notes": post.get("notes"),
        }

        boiler_model_id = post.get("boiler_model_id")
        if boiler_model_id and boiler_model_id.isdigit():
            model = request.env["sre.boiler.model"].sudo().browse(int(boiler_model_id))
            if model.exists():
                vals["boiler_model_id"] = model.id
                vals["boiler_manufacturer_id"] = model.manufacturer_id.id

        equipment = request.env["sre.customer.equipment"].sudo().create(vals)
        return request.redirect(f"/my/plant/{equipment.id}?created=1")

    @http.route("/my/plant/delete/<int:equipment_id>", type="http", auth="user", website=True, methods=["POST"])
    def portal_my_equipment_delete(self, equipment_id=None, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        equipment = request.env["sre.customer.equipment"].sudo().browse(equipment_id)
        if not equipment.exists() or equipment.partner_id.id != partner.id:
            raise NotFound()
        equipment.unlink()
        return request.redirect("/my/plant?deleted=1")

    @http.route("/my/plant/<int:equipment_id>/add-all-spares", type="http", auth="user", website=True, methods=["POST", "GET"])
    def portal_my_equipment_add_all_spares(self, equipment_id=None, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        equipment = request.env["sre.customer.equipment"].sudo().browse(equipment_id)
        if not equipment.exists() or equipment.partner_id.id != partner.id:
            raise NotFound()

        basket_key = "sre_rfq_basket_%s" % request.website.id
        basket = request.session.get(basket_key, {})

        added_count = 0
        for tmpl in equipment.compatible_part_ids:
            variant = tmpl.product_variant_id or tmpl.product_variant_ids[:1]
            if variant and variant.sale_ok:
                pid_str = str(variant.id)
                basket[pid_str] = basket.get(pid_str, 0) + 1
                added_count += 1

        request.session[basket_key] = basket
        return request.redirect(f"/rfq?plant_spares_added={added_count}")
