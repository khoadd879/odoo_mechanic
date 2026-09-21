{
    "name": "Mechanic Workshop",
    "version": "19.0.1.13.0",
    "category": "Sales",
    "summary": "SRE technical catalog and customer RFQ on native Odoo Sales.",
    "description": """
Mechanic Workshop
=================

Technical catalog, public RFQ basket, CRM intake and staff-controlled
quotation creation. Native Odoo owns all sales and operational flows.

Sprint 1 catalogue taxonomy:
  * 8 Navigation Pillars (brief §04)
  * Product Family per Pillar with Attribute Profile (brief §07)
  * Industry and Application taxonomies (brief §14/§15)
  * OEM Part Number scaffold for search and Cross Reference (brief §05/§12)

Sprint 1 visual (McMaster-Carr reference):
  * 4-column table-row tiles, monospace SKU/MPN, dense spec list.
  * Industrial-blue pillar top nav, sticky filter rail, per-page
    section header, pagination footer, lead-magnet CTA card.
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
        "data/sre_home_seed.xml",
        "data/sre_pim_seed.xml",
        "data/sre_boiler_seed.xml",
        "data/sre_cross_reference_seed.xml",
        "data/sre_documents_seed.xml",
        "data/sre_portal_seed.xml",
        "views/sre_navigation_pillar_views.xml",
        "views/sre_product_family_views.xml",
        "views/sre_attribute_profile_views.xml",
        "views/sre_industry_views.xml",
        "views/sre_oem_pn_views.xml",
        "views/sre_boiler_views.xml",
        "views/sre_cross_reference_views.xml",
        "views/sre_product_document_views.xml",
        "views/sre_customer_equipment_views.xml",
        "views/sre_technical_library_views.xml",
        "views/sre_rfq_unknown_part.xml",
        "views/sre_portal_views.xml",
        "views/website_sale_header.xml",
        "views/website_sale_search.xml",
        "views/sre_catalog.xml",
        "views/sre_home.xml",
        "views/sre_taxonomy_views.xml",
        "views/sre_boiler_finder_views.xml",
        "views/sre_cross_reference_website.xml",
        "views/rfq_backend.xml",
        "views/website_sale_product_tile.xml",
        "views/website_sale_product_detail.xml",
        "views/rfq_website.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "mechanic_workshop/static/src/js/rfq.js",
            "mechanic_workshop/static/src/js/sre_search.js",
            "mechanic_workshop/static/src/js/sre_catalog_filters.js",
            "mechanic_workshop/static/src/js/sre_document_download.js",
            "mechanic_workshop/static/src/scss/sre_tokens.scss",
            "mechanic_workshop/static/src/scss/sre_topnav.scss",
            "mechanic_workshop/static/src/scss/sre_tile.scss",
            "mechanic_workshop/static/src/scss/sre_category.scss",
            "mechanic_workshop/static/src/scss/sre_home.scss",
            "mechanic_workshop/static/src/scss/sre_search.scss",
            "mechanic_workshop/static/src/scss/sre_section.scss",
            "mechanic_workshop/static/src/scss/sre_site.scss",
        ]
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
