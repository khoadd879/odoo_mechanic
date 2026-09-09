"""Public-facing computed fields on ``product.template``.

The SRE public catalog (see ``views/website_sale_product_tile.xml``
and ``views/website_sale_product_detail.xml``) needs to display the
manufacturer's *public name* on every product page. The default Odoo
19 record rule on ``res.partner`` (``id child_of
user.commercial_partner_id``) blocks the public user from reading
any partner outside its own hierarchy, so the template cannot simply
use ``t-field="product.manufacturer_id.display_name"`` — the access
check fires during the M2O dereference and the page returns 403.

We work around the access rule with a ``compute_sudo=True`` field
that returns a plain ``Char``. The field is computed as superuser
(so it can read ``res.partner``), but the public user only ever
sees the cached string. We grant no broader access to
``res.partner`` records. The brand side already works because the
OCA ``product_brand`` module grants read on ``product.brand`` to
``base.group_public``; the same is NOT true for ``res.partner``.

We do not leak supplier hierarchy: the field returns only
``display_name`` (the company name), never ``email`` / ``phone`` /
``vat`` / supplierinfo. The brief (§17) requires that Brand be
public info and that supplier / source information never be
exposed.

Sprint 1 extension: add the SRE Family / Industry / Application M2M
relations and an inverse O2M for OEM Part Numbers so the search and
category page can use them as facets and as exact-match search
fields.

The canonical multi-field search and its tiered suggestions live in
``controllers/catalog.py`` and ``controllers/search_suggest.py``. We
also extend Odoo 19's native ``_search_get_detail`` here so other native
website search consumers can include the direct public Char fields.
"""

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    manufacturer_public_name = fields.Char(
        string="Manufacturer (public)",
        compute="_compute_manufacturer_public_name",
        store=True,
        index=True,
        compute_sudo=True,
        help=(
            "Public-safe manufacturer name. Stored and indexed so the "
            "public ``/shop`` search can ``ilike`` it. Computed as "
            "superuser to bypass the default ``res.partner`` record "
            "rule; the public user only ever sees the cached display "
            "name string. No phone, email or supplier info exposed."
        ),
    )

    family_id = fields.Many2one(
        "sre.product.family",
        string="Product Family",
        ondelete="set null",
        index=True,
        help=(
            "SRE business pillar that scopes the technical filters "
            "and the navigation entry for this product. Brief §04."
        ),
    )
    industry_ids = fields.Many2many(
        "sre.industry",
        "sre_industry_product_rel",
        "product_tmpl_id",
        "industry_id",
        string="Industries",
        help="Brief §14: a product may serve many industries.",
    )
    application_ids = fields.Many2many(
        "sre.application",
        "sre_application_product_rel",
        "product_tmpl_id",
        "application_id",
        string="Applications",
        help="Brief §15: a product may serve many applications.",
    )
    sre_oem_pn_ids = fields.One2many(
        "sre.oem.pn",
        "product_tmpl_id",
        string="OEM part numbers",
    )
    sre_public_oem_part_numbers = fields.Char(
        string="OEM part numbers (public)",
        compute="_compute_sre_public_oem_part_numbers",
        compute_sudo=True,
        store=True,
        index=True,
        help=(
            "Public-safe, searchable OEM part-number list. Internal OEM "
            "notes and manufacturer records are never exposed to website users."
        ),
    )

    @api.depends("manufacturer_id.display_name")
    def _compute_manufacturer_public_name(self) -> None:
        for product in self:
            manufacturer = product.manufacturer_id
            product.manufacturer_public_name = (
                manufacturer.display_name if manufacturer else False
            )

    @api.depends(
        "sre_oem_pn_ids.oem_part_number",
        "sre_oem_pn_ids.active",
    )
    def _compute_sre_public_oem_part_numbers(self) -> None:
        """Cache only public OEM identifiers on the product template."""

        for product in self:
            part_numbers = product.sre_oem_pn_ids.filtered("active").mapped(
                "oem_part_number"
            )
            product.sre_public_oem_part_numbers = ", ".join(part_numbers)

    # -- Search detail extension ------------------------------------------
    # We extend the Odoo 19 ``_search_get_detail`` so the fuzzy search
    # field list (used by ``_search_build_domain``) also includes
    # MPN (``manufacturer_pref``) and the stored public manufacturer
    # name. Only direct Char/Text fields are added: the Odoo 19
    # fuzzy trigram similarity engine only handles Many2many and
    # One2many traversals, never Many2one, and raises
    # ``AssertionError: '' invalid for SQL.identifier()`` on M2O
    # paths. The canonical SRE catalog therefore handles Brand and the
    # stored OEM projection explicitly in its own domain.
    def _search_get_detail(
        self,
        website: models.Model,
        order: str,
        options: dict,
    ) -> dict:
        detail = super()._search_get_detail(website, order, options)
        sre_fields = [
            "manufacturer_pref",
            "manufacturer_public_name",
            "sre_public_oem_part_numbers",
        ]
        for f in sre_fields:
            if f not in detail["search_fields"]:
                detail["search_fields"].append(f)
        return detail
