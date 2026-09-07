{
    "name": "Mechanic Workshop",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Mechanic workshop scaffold built on native Odoo 19 modules.",
    "description": """
Mechanic Workshop
=================

Empty starter addon for the Mechanic Workshop project. The module
ships with no models, views, or data so it can be filled feature by
feature as documented in ``docs/FEATURE_LIST.json``.
    """,
    "author": "Mechanic Workshop",
    "license": "LGPL-3",
    "depends": [
        "base",
        "website",
        "website_sale",
        "product",
        "product_brand",
        "product_manufacturer",
    ],
    "data": [
        "views/website_sale_product_tile.xml",
        "views/website_sale_product_detail.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
