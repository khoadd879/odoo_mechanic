"""SRE visual preview — dump the live catalog page rendered through
the same controller chain the public storefront uses.

Developer tool, mounted at ``/sre/preview``. It delegates to
``SreCatalog.catalog`` so the McMaster-Carr pillar nav, table-row
tiles, view-mode toggle and family filter rail all materialise
without us duplicating any rendering logic. The output is exactly
what a visitor to ``/sre/catalog`` sees in their browser, but
rendered on demand from the live database.

The HTML response is the same as ``/sre/catalog``; it relies on the
standard Odoo asset pipeline. To obtain a fully self-contained
snapshot that you can open offline in any browser, run the helper
script ``docs/sre_visual_evidence/build_snapshot.sh`` which
downloads the live page and inlines the SCSS.
"""
from __future__ import annotations

from odoo import http

from .catalog import SreCatalog


class SrePreview(SreCatalog):
    @http.route(
        "/sre/preview",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
        csrf=False,
    )
    def preview(self, **kw):
        return super().catalog(
            pillar_slug=kw.get("pillar"),
            family_slug=kw.get("family"),
            **kw,
        )