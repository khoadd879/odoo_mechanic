"""Centralized Technical Library & Document Governance Controller (Brief §16 — P1).

Provides:
1. Public Technical Library discovery page (/sre/documents and /technical-library)
2. JSON-RPC gated document request endpoint with CRM Lead creation
"""

from __future__ import annotations

import re
from odoo import http, _
from odoo.http import request


class SreTechnicalLibrary(http.Controller):
    """Centralized Technical Library Controller."""

    @http.route(
        [
            "/sre/documents",
            "/technical-library",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def technical_library(
        self,
        q: str | None = None,
        type: str | None = None,
        brand: str | None = None,
        format: str | None = None,
        **kw: object,
    ) -> http.Response:
        """Render the centralized technical documents & CAD library."""
        Doc = request.env["product.document"].sudo()
        Brand = request.env["product.brand"].sudo()

        base_domain = [
            ("active", "=", True),
            ("shown_on_product_page", "=", True),
            ("governance_type", "!=", "internal"),
        ]

        # Calculate counts per document type for badge filters
        type_counts = {
            "all": Doc.search_count(base_domain),
            "datasheet": Doc.search_count(base_domain + [("document_type", "=", "datasheet")]),
            "cad_drawing": Doc.search_count(base_domain + [("document_type", "=", "cad_drawing")]),
            "manual": Doc.search_count(base_domain + [("document_type", "=", "manual")]),
            "certificate": Doc.search_count(base_domain + [("document_type", "=", "certificate")]),
            "brochure": Doc.search_count(base_domain + [("document_type", "=", "brochure")]),
        }

        domain = list(base_domain)

        if type and type in ("datasheet", "cad_drawing", "manual", "certificate", "brochure"):
            domain.append(("document_type", "=", type))

        if format:
            domain.append(("cad_format", "=", format))

        brand_id = None
        if brand:
            try:
                brand_id = int(brand)
                domain.append(("product_tmpl_id.product_brand_id", "=", brand_id))
            except (ValueError, TypeError):
                matched_brand = Brand.search([("name", "ilike", brand)], limit=1)
                if matched_brand:
                    brand_id = matched_brand.id
                    domain.append(("product_tmpl_id.product_brand_id", "=", brand_id))

        if q:
            term = q.strip()
            domain.extend([
                "|", "|", "|",
                ("name", "ilike", term),
                ("product_tmpl_id.name", "ilike", term),
                ("product_tmpl_id.default_code", "ilike", term),
                ("product_tmpl_id.product_brand_id.name", "ilike", term),
            ])

        documents = Doc.search(domain, order="sequence, id desc")

        # Brands available with published documents
        all_docs = Doc.search(base_domain)
        available_brands = all_docs.mapped("product_tmpl_id.product_brand_id").filtered("id")

        return request.render(
            "mechanic_workshop.technical_library_page",
            {
                "documents": documents,
                "current_q": q or "",
                "current_type": type or "all",
                "current_brand": brand_id,
                "current_format": format or "",
                "type_counts": type_counts,
                "available_brands": available_brands,
            },
        )

    @http.route(
        "/sre/document/gated-request",
        type="jsonrpc",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def gated_document_request(
        self,
        document_id: int,
        contact_name: str,
        company_name: str,
        email: str,
        phone: str = "",
        notes: str = "",
        **kw: object,
    ) -> dict:
        """Handle B2B gated document download request: validate, create CRM lead, return download url."""
        if not contact_name or not company_name or not email:
            return {"success": False, "error": _("Contact name, company name and email are required.")}

        email_clean = email.strip()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email_clean):
            return {"success": False, "error": _("Please enter a valid business email address.")}

        try:
            doc_id = int(document_id)
        except (ValueError, TypeError):
            return {"success": False, "error": _("Invalid document identifier.")}

        document = request.env["product.document"].sudo().browse(doc_id).exists()
        if not document or not document.active or document.governance_type == "internal":
            return {"success": False, "error": _("This document is not available for download.")}

        product = document.product_tmpl_id

        # Create CRM Lead for commercial follow-up
        lead_vals = {
            "name": f"Document Download: {document.name} — {company_name.strip()}",
            "type": "opportunity",
            "contact_name": contact_name.strip(),
            "partner_name": company_name.strip(),
            "email_from": email_clean,
            "phone": (phone or "").strip(),
            "company_id": request.website.company_id.id,
            "description": (
                f"Technical Document Download Request (Gated B2B Access):\n"
                f"• Document: {document.name}\n"
                f"• Type: {dict(document._fields['document_type'].selection).get(document.document_type, document.document_type)}\n"
                f"• Format: {document.cad_format.upper()}\n"
                f"• Product: {product.name if product else 'N/A'}\n"
                f"• SRE SKU: {product.default_code if product else 'N/A'}\n"
                f"• Project Notes: {notes.strip() if notes else 'None'}\n"
            ),
        }
        request.env["crm.lead"].sudo().create(lead_vals)

        # Register download hit
        document.action_register_download()

        # Build download URL
        if product:
            download_url = f"/shop/{product.id}/document/{document.id}"
        else:
            download_url = f"/web/content/{document.ir_attachment_id.id}?download=true"

        return {
            "success": True,
            "download_url": download_url,
            "document_name": document.name,
            "format": document.cad_format.upper(),
        }
