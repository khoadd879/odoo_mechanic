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
"""

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    manufacturer_public_name = fields.Char(
        string="Manufacturer (public)",
        compute="_compute_manufacturer_public_name",
        compute_sudo=True,
        help=(
            "Public-safe manufacturer name. Computed as superuser so "
            "the public website can show it without granting broader "
            "read access to res.partner. Returns only display_name; "
            "never email, phone, address, or supplier info."
        ),
    )

    def _compute_manufacturer_public_name(self):
        for product in self:
            manufacturer = product.manufacturer_id
            product.manufacturer_public_name = (
                manufacturer.display_name if manufacturer else False
            )
