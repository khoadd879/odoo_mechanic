from __future__ import annotations

import base64
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
        uploaded_file = request.httprequest.files.get("nameplate_file")
        if uploaded_file and uploaded_file.filename:
            file_data = uploaded_file.read()
            if len(file_data) > 10 * 1024 * 1024:
                raise BadRequest("Nameplate file size exceeds 10MB limit")
            values["nameplate_image"] = base64.b64encode(file_data)
            values["nameplate_filename"] = uploaded_file.filename[:250]
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

    @http.route("/rfq/unknown-part", type="http", auth="public", website=True, methods=["GET"], sitemap=True)
    def unknown_part_page(self, **kw):
        """Render dedicated Unknown Part Identification wizard/form."""
        return request.render("mechanic_workshop.rfq_unknown_part_page", {})

    @http.route("/rfq/unknown-part/submit", type="http", auth="public", website=True, methods=["POST"])
    def unknown_part_submit(self, **post):
        """Handle Unknown Part identification request submission."""
        values = {}
        for key in ("contact_name", "company_name", "email", "phone", "project_name", "project_location", "notes",
                    "equipment_make_model", "operating_medium", "connection_type"):
            values[key] = str(post.get(key, "")).strip()
            if len(values[key]) > (4000 if key == "notes" else 250):
                raise BadRequest("Input too long")

        if not all(values[k] for k in ("contact_name", "company_name", "email")):
            raise BadRequest("Company, contact name and email are required")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values["email"]):
            raise BadRequest("Invalid email")

        for num_key in ("operating_pressure", "operating_temperature"):
            val_str = str(post.get(num_key, "")).strip()
            if val_str:
                try:
                    values[num_key] = float(val_str)
                except (ValueError, TypeError):
                    pass

        delivery = post.get("required_delivery_date")
        if delivery:
            try:
                date.fromisoformat(delivery)
                values["required_delivery_date"] = delivery
            except ValueError:
                pass

        values.update({
            "is_unknown_part": True,
            "company_id": request.website.company_id.id,
            "website_id": request.website.id,
        })

        uploaded_file = request.httprequest.files.get("nameplate_file")
        if uploaded_file and uploaded_file.filename:
            file_data = uploaded_file.read()
            if len(file_data) > 10 * 1024 * 1024:
                raise BadRequest("Nameplate file size exceeds 10MB limit")
            values["nameplate_image"] = base64.b64encode(file_data)
            values["nameplate_filename"] = uploaded_file.filename[:250]

        Rfq = request.env["sre.rfq"].sudo().with_company(request.website.company_id)
        rfq = Rfq.create(values)
        rfq._create_opportunity()

        request.session[self._basket_key() + "_reference"] = rfq.name
        return request.redirect("/rfq/thanks")

    def _match_and_add_to_basket(self, items, basket):
        """Match list of (part_term, qty) tuples against SKU, MPN, Cross References."""
        Product = request.env["product.product"].sudo()
        Xref = request.env["sre.product.cross.reference"].sudo()
        matched = []
        unmatched = []

        for part_term, qty in items:
            if not part_term:
                continue

            # 1. Direct SKU match
            prod = Product.search([
                ("default_code", "=ilike", part_term),
                ("active", "=", True),
                ("sale_ok", "=", True),
                ("product_tmpl_id.is_published", "=", True),
            ], limit=1)

            # 2. Manufacturer PN match
            if not prod:
                prod = Product.search([
                    ("manufacturer_pref", "=ilike", part_term),
                    ("active", "=", True),
                    ("sale_ok", "=", True),
                    ("product_tmpl_id.is_published", "=", True),
                ], limit=1)

            # 3. Cross Reference match
            if not prod:
                xref_rec = Xref.search([
                    ("source_part_number", "=ilike", part_term),
                    ("active", "=", True),
                ], limit=1)
                if xref_rec and xref_rec.target_product_id:
                    prod = xref_rec.target_product_id.product_variant_id

            if prod and prod.sale_ok:
                pid_str = str(prod.id)
                current_qty = basket.get(pid_str, 0)
                basket[pid_str] = self._quantity(current_qty + qty)
                matched.append({
                    "sku": prod.default_code or prod.name,
                    "name": prod.name,
                    "quantity": qty,
                })
            else:
                unmatched.append({
                    "term": part_term,
                    "quantity": qty,
                })

        return matched, unmatched

    @http.route("/rfq/api/bom-parse", type="jsonrpc", auth="public", website=True, methods=["POST"])
    def bom_parse(self, text="", **kw):
        """Parse raw multi-line BOM lines (SKU/MPN, Quantity) and add to RFQ basket."""
        if not text or not str(text).strip():
            return {"success": False, "error": _("Please enter at least one line with SKU and quantity.")}

        basket = dict(request.session.get(self._basket_key(), {}))
        lines = str(text).strip().splitlines()
        items = []

        for raw_line in lines[:100]:  # Limit to 100 lines max
            line = raw_line.strip()
            if not line or line.startswith(("#", "//")):
                continue
            tokens = re.split(r"[,;\t|]+", line)
            part_term = tokens[0].strip()
            qty = 1.0
            if len(tokens) > 1:
                try:
                    qty = self._quantity(tokens[1].strip())
                except Exception:
                    qty = 1.0
            items.append((part_term, qty))

        matched, unmatched = self._match_and_add_to_basket(items, basket)
        request.session[self._basket_key()] = basket

        return {
            "success": True,
            "added_count": len(matched),
            "unmatched_count": len(unmatched),
            "basket_total_items": len(basket),
            "matched": matched,
            "unmatched": unmatched,
        }

    @http.route("/rfq/api/bom-upload", type="http", auth="public", website=True, methods=["POST"], csrf=False)
    def bom_upload(self, **post):
        """Upload and parse Excel (.xlsx, .xls) or CSV BOM file into RFQ basket."""
        import io
        import csv

        bom_file = request.httprequest.files.get("bom_file")
        if not bom_file or not bom_file.filename:
            return request.make_json_response({"success": False, "error": _("No file was uploaded.")})

        filename = bom_file.filename.lower()
        items = []

        try:
            if filename.endswith((".csv", ".txt")):
                content = bom_file.read().decode("utf-8", errors="ignore")
                reader = csv.reader(io.StringIO(content))
                for row in reader:
                    if not row or not any(row):
                        continue
                    part_term = str(row[0]).strip()
                    if part_term.lower() in ("sku", "part number", "mpn", "part_number", "part", "mã hàng", "mã vật tư"):
                        continue
                    qty = 1.0
                    if len(row) > 1:
                        try:
                            qty = self._quantity(str(row[1]).strip())
                        except Exception:
                            qty = 1.0
                    items.append((part_term, qty))

            elif filename.endswith((".xlsx", ".xls")):
                import openpyxl
                file_bytes = io.BytesIO(bom_file.read())
                wb = openpyxl.load_workbook(filename=file_bytes, data_only=True)
                sheet = wb.active
                for row in sheet.iter_rows(values_only=True):
                    if not row or not any(row):
                        continue
                    part_val = row[0]
                    if part_val is None:
                        continue
                    part_term = str(part_val).strip()
                    if part_term.lower() in ("sku", "part number", "mpn", "part_number", "part", "mã hàng", "mã vật tư"):
                        continue
                    qty = 1.0
                    if len(row) > 1 and row[1] is not None:
                        try:
                            qty = self._quantity(str(row[1]).strip())
                        except Exception:
                            qty = 1.0
                    items.append((part_term, qty))
            else:
                return request.make_json_response({
                    "success": False,
                    "error": _("Unsupported file format. Please upload .xlsx, .xls, or .csv file.")
                })
        except Exception as e:
            return request.make_json_response({
                "success": False,
                "error": f"Error parsing spreadsheet file: {str(e)}"
            })

        if not items:
            return request.make_json_response({
                "success": False,
                "error": _("No valid part numbers found in the uploaded file.")
            })

        basket = dict(request.session.get(self._basket_key(), {}))
        matched, unmatched = self._match_and_add_to_basket(items[:200], basket)
        request.session[self._basket_key()] = basket

        return request.make_json_response({
            "success": True,
            "added_count": len(matched),
            "unmatched_count": len(unmatched),
            "basket_total_items": len(basket),
            "matched": matched,
            "unmatched": unmatched,
        })
