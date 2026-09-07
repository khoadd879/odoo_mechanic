{
    "name": "Mechanic Workshop",
    "version": "19.0.1.1.0",
    "category": "Sales",
    "summary": "SRE technical catalog and customer RFQ on native Odoo Sales.",
    "description": """
Mechanic Workshop
=================

Technical catalog, public RFQ basket, CRM intake and staff-controlled
quotation creation. Native Odoo owns all sales and operational flows.
    """,
    "author": "Mechanic Workshop",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale_management",
        "sale_crm",
        "website",
        "website_sale",
        "product",
        "product_brand",
        "product_manufacturer",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/rfq_backend.xml",
        "views/website_sale_product_tile.xml",
        "views/website_sale_product_detail.xml",
        "views/rfq_website.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
