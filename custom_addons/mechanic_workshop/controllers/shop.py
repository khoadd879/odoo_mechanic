"""SRE shop controller — redirect /shop to /sre/catalog.

The canonical catalog route is /sre/catalog (see controllers/catalog.py).
The native /shop, /shop/pillar/<slug>, /shop/family/<slug> URLs now
return HTTP 301 to the matching /sre/catalog[...] URL, preserving the
query string so /shop?search=DMV-001 lands on /sre/catalog?search=DMV-001.
"""
from __future__ import annotations

from odoo import http
from odoo.http import request


class SreWebsiteSale(http.Controller):
    @http.route(
        [
            "/shop",
            "/shop/page/<int:page>",
            "/shop/pillar/<string:pillar_slug>",
            "/shop/pillar/<string:pillar_slug>/page/<int:page>",
            "/shop/family/<string:family_slug>",
            "/shop/family/<string:family_slug>/page/<int:page>",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def shop(self, page=0, pillar_slug=None, family_slug=None, **kw):
        target = "/sre/catalog"
        if pillar_slug:
            target = f"/sre/catalog/pillar/{pillar_slug}"
        elif family_slug:
            target = f"/sre/catalog/family/{family_slug}"
        if page:
            target = f"{target}?page={page}"
        qs = request.httprequest.query_string.decode("utf-8")
        if qs:
            joiner = "&" if "?" in target else "?"
            target = f"{target}{joiner}{qs}"
        return request.redirect(target, code=301, local=False)