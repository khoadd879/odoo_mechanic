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
    sre_category_id = fields.Many2one(
        related="family_id.category_id",
        string="SRE Category",
        store=True,
        readonly=True,
        index=True,
        help="Parent SRE Category (Level 2) derived from family.",
    )
    product_type_id = fields.Many2one(
        "sre.product.type",
        string="SRE Product Type",
        ondelete="set null",
        index=True,
        help="Specific product type under the family (Level 4).",
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
    boiler_mapping_ids = fields.One2many(
        "sre.boiler.part.mapping",
        "product_tmpl_id",
        string="Boiler Compatibility Mappings",
        help="Brief §11: Boilers and subsystems this part is verified compatible with.",
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
    public_price_approved = fields.Boolean(
        string="Public Price Approved",
        default=False,
        index=True,
        help=(
            "Brief §11: When checked, the public catalog displays the "
            "list_price. When unchecked (default), price is hidden and "
            "B2B Quote on Request is shown."
        ),
    )
    operating_pressure_min = fields.Float(
        string="Min Operating Pressure (bar)",
        digits=(10, 2),
        index=True,
        default=0.0,
        help="Brief §07: Minimum operating/working pressure in bar.",
    )
    operating_pressure_max = fields.Float(
        string="Max Operating Pressure (bar)",
        digits=(10, 2),
        index=True,
        default=0.0,
        help="Brief §07: Maximum operating/rated pressure in bar.",
    )
    operating_temp_min = fields.Float(
        string="Min Operating Temp (°C)",
        digits=(10, 2),
        index=True,
        default=0.0,
        help="Brief §07: Minimum operating temperature in degrees Celsius.",
    )
    operating_temp_max = fields.Float(
        string="Max Operating Temp (°C)",
        digits=(10, 2),
        index=True,
        default=0.0,
        help="Brief §07: Maximum operating temperature in degrees Celsius.",
    )
    flow_rate_min = fields.Float(
        string="Min Flow Rate (m³/h)",
        digits=(10, 2),
        index=True,
        default=0.0,
        help="Brief §07: Minimum operating flow rate in cubic meters per hour.",
    )
    flow_rate_max = fields.Float(
        string="Max Flow Rate (m³/h)",
        digits=(10, 2),
        index=True,
        default=0.0,
        help="Brief §07: Maximum operating flow rate in cubic meters per hour.",
    )
    cross_reference_ids = fields.One2many(
        "sre.product.cross.reference",
        "target_product_id",
        string="Cross References",
    )
    cross_reference_count = fields.Integer(
        compute="_compute_cross_reference_count",
        string="Cross References Count",
    )

    @api.depends("cross_reference_ids")
    def _compute_cross_reference_count(self) -> None:
        for product in self:
            product.cross_reference_count = len(product.cross_reference_ids)

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

    def _get_b2b_contract_price(self, user=None):
        """Brief §18: Returns B2B contract price if user has an assigned pricelist, else False."""
        user = user or self.env.user
        if not user or user._is_public():
            return False
        partner = user.partner_id
        pricelist = partner.property_product_pricelist
        if not pricelist:
            return False
        self.ensure_one()
        if self.list_price <= 0:
            return False
        return self.with_context(pricelist=pricelist.id)._get_contextual_price()

    def _get_technical_specifications(self) -> dict[str, object]:
        """Return structured technical specifications grouped into Key and Additional Specs.

        Attributes are filtered by is_display_shown=True and sorted by sequence defined in the
        family's Attribute Profile.
        """
        self.ensure_one()
        key_specs: list[dict[str, object]] = []
        additional_specs: list[dict[str, object]] = []

        # 1. Base measured operating conditions
        if self.operating_pressure_max:
            val = (
                f"{self.operating_pressure_min:.1f} – {self.operating_pressure_max:.1f} bar"
                if self.operating_pressure_min
                else f"Up to {self.operating_pressure_max:.1f} bar"
            )
            key_specs.append({
                "name": "Operating Pressure",
                "value": val,
                "is_key": True,
                "sequence": 1,
            })

        if self.operating_temp_max or self.operating_temp_min:
            val = f"{self.operating_temp_min:.0f} to {self.operating_temp_max:.0f} °C"
            key_specs.append({
                "name": "Operating Temperature",
                "value": val,
                "is_key": True,
                "sequence": 2,
            })

        if self.flow_rate_max:
            val = (
                f"{self.flow_rate_min:.1f} – {self.flow_rate_max:.1f} m³/h"
                if self.flow_rate_min
                else f"Up to {self.flow_rate_max:.1f} m³/h"
            )
            key_specs.append({
                "name": "Operating Flow Rate",
                "value": val,
                "is_key": True,
                "sequence": 3,
            })

        # 2. Level 4 Product Type
        if self.product_type_id:
            key_specs.append({
                "name": "Product Type",
                "value": self.product_type_id.name,
                "is_key": True,
                "sequence": 4,
            })

        # 3. Dynamic attributes from Attribute Profile
        profile = (
            self.family_id.attribute_profile_id.sudo()
            if self.family_id and self.family_id.attribute_profile_id
            else None
        )
        profile_lines_map: dict[int, object] = {}
        if profile:
            for pl in profile.line_ids:
                profile_lines_map[pl.attribute_id.id] = pl

        for p_line in self.attribute_line_ids:
            attr = p_line.attribute_id
            values_str = ", ".join(p_line.value_ids.mapped("name"))
            if not values_str:
                continue

            if profile_lines_map:
                p_meta = profile_lines_map.get(attr.id)
                if p_meta:
                    if not p_meta.is_display_shown:
                        continue
                    spec_item = {
                        "name": attr.name,
                        "value": values_str,
                        "is_key": p_meta.is_required,
                        "sequence": p_meta.sequence or attr.sequence or 10,
                    }
                    if p_meta.is_required:
                        key_specs.append(spec_item)
                    else:
                        additional_specs.append(spec_item)
                else:
                    additional_specs.append({
                        "name": attr.name,
                        "value": values_str,
                        "is_key": False,
                        "sequence": attr.sequence or 20,
                    })
            else:
                additional_specs.append({
                    "name": attr.name,
                    "value": values_str,
                    "is_key": False,
                    "sequence": attr.sequence or 20,
                })

        key_specs.sort(key=lambda x: (x.get("sequence", 10), str(x.get("name", ""))))
        additional_specs.sort(key=lambda x: (x.get("sequence", 10), str(x.get("name", ""))))

        return {
            "key_specs": key_specs,
            "additional_specs": additional_specs,
            "all_specs": key_specs + additional_specs,
            "has_specs": bool(key_specs or additional_specs),
        }

