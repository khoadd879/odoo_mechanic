from __future__ import annotations

import math
import re
import secrets
from datetime import date
from werkzeug.exceptions import BadRequest
from odoo import http, Command, _
from odoo.http import request
from odoo.tools import SQL, float_round


class CustomerRfq(http.Controller):
    def _basket_key(self):
        return "sre_rfq_basket_%s" % request.website.id

    def _products(self, ids):
        # sudo is limited to catalog products that are explicitly public here.
        return request.env["product.product"].sudo().search([
            ("id", "in", ids), ("active", "=", True), ("sale_ok", "=", True),
            ("product_tmpl_id.is_published", "=", True),
            ("product_tmpl_id.website_id", "in", [False, request.website.id]),
            ("company_id", "in", [False, request.website.company_id.id]),
        ])

    def _quantity(self, value):
        try:
            qty = float(value)
        except (ValueError, TypeError):
            raise BadRequest("Invalid quantity") from None
        if not math.isfinite(qty) or not 0 < qty <= 1000000:
            raise BadRequest("Quantity must be positive and at most 1,000,000")
        digits = request.env["decimal.precision"].precision_get("Product Unit")
        qty = float_round(qty, precision_digits=digits)
        if qty <= 0:
            raise BadRequest("Quantity is below the supported precision")
        return qty

    @http.route("/rfq", type="http", auth="public", website=True, methods=["GET"], sitemap=False)
    def basket(self, **kw):
        basket = request.session.get(self._basket_key(), {})
        products = self._products([int(key) for key in basket])
        removed = len(products) != len(basket)
        if removed:
            basket = {str(p.id): basket[str(p.id)] for p in products}
            request.session[self._basket_key()] = basket
        token_key = self._basket_key() + "_token"
        if not request.session.get(token_key):
            request.session[token_key] = secrets.token_hex(32)
        return request.render("mechanic_workshop.rfq_basket", {
            "lines": [(p, basket[str(p.id)]) for p in products],
            "submission_key": request.session[token_key], "removed": removed,
        })

    @http.route("/rfq/add", type="http", auth="public", website=True, methods=["POST"])
    def add(self, product_id=None, quantity="1", **kw):
        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            raise BadRequest("Invalid product") from None
        if not self._products([product_id]):
            raise BadRequest("Product is not available for RFQ")
        basket = dict(request.session.get(self._basket_key(), {}))
        if str(product_id) not in basket and len(basket) >= 100:
            raise BadRequest("Maximum 100 products per request")
        if not basket and request.session.get(self._basket_key() + "_reference"):
            request.session[self._basket_key() + "_token"] = secrets.token_hex(32)
            request.session.pop(self._basket_key() + "_reference", None)
        basket[str(product_id)] = self._quantity(basket.get(str(product_id), 0) + self._quantity(quantity))
        request.session[self._basket_key()] = basket
        if kw.get("ajax") == "1":
            return request.make_json_response({"line_count": len(basket)})
        return request.redirect("/rfq")

    @http.route("/rfq/update", type="http", auth="public", website=True, methods=["POST"])
    def update(self, product_id=None, quantity="1", remove=None, **kw):
        basket = dict(request.session.get(self._basket_key(), {}))
        if product_id not in basket:
            raise BadRequest("Unknown basket line")
        if remove:
            basket.pop(product_id)
        else:
            basket[product_id] = self._quantity(quantity)
        request.session[self._basket_key()] = basket
        return request.redirect("/rfq")

    @http.route("/rfq/submit", type="http", auth="public", website=True, methods=["POST"])
    def submit(self, submission_key=None, **post):
        expected = request.session.get(self._basket_key() + "_token", "")
        if not expected or not secrets.compare_digest(str(submission_key or ""), expected):
            raise BadRequest("Please reload your RFQ before submitting")
        # Lock by token across requests. Unique constraint is an additional safeguard.
        request.env.cr.execute(SQL("SELECT pg_advisory_xact_lock(hashtext(%s))", expected))
        Rfq = request.env["sre.rfq"].sudo().with_company(request.website.company_id)
        existing = Rfq.search([("submission_key", "=", expected)], limit=1)
        if existing:
            request.session[self._basket_key() + "_reference"] = existing.name
            return request.redirect("/rfq/thanks")
        values = {}
        for key in ("contact_name", "company_name", "email", "phone", "project_name", "project_location", "notes"):
            values[key] = str(post.get(key, "")).strip()
            if len(values[key]) > (4000 if key == "notes" else 250):
                raise BadRequest("Input too long")
        if not all(values[k] for k in ("contact_name", "company_name", "email")):
            raise BadRequest("Company, contact name and email are required")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values["email"]):
            raise BadRequest("Invalid email")
        delivery = post.get("required_delivery_date")
        if delivery:
            try:
                date.fromisoformat(delivery)
            except ValueError:
                raise BadRequest("Invalid delivery date") from None
            values["required_delivery_date"] = delivery
        basket = request.session.get(self._basket_key(), {})
        products = self._products([int(key) for key in basket])
        if not products or len(products) != len(basket):
            raise BadRequest("Your basket is empty or contains unavailable products")
        values.update({
            "company_id": request.website.company_id.id, "website_id": request.website.id,
            "submission_key": expected,
            "line_ids": [Command.create({"product_id": p.id, "quantity": self._quantity(basket[str(p.id)])}) for p in products],
        })
        # Do not resolve an existing customer from an unverified email.
        rfq = Rfq.create(values)
        rfq._create_opportunity()
        request.session[self._basket_key()] = {}
        request.session[self._basket_key() + "_reference"] = rfq.name
        return request.redirect("/rfq/thanks")

    @http.route("/rfq/thanks", type="http", auth="public", website=True, methods=["GET"], sitemap=False)
    def thanks(self, **kw):
        reference = request.session.get(self._basket_key() + "_reference")
        if not reference:
            return request.redirect("/rfq")
        return request.render("mechanic_workshop.rfq_thanks", {"reference": reference})
