"""Website extension that exposes published SRE pillars to templates.

Templates iterate ``request.website.sre_visible_pillars``. Defining
the helper on ``website`` keeps the template side free of model
queries; a single ``compute`` returns the published+active pillars
ordered by sequence.
"""

from __future__ import annotations

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    sre_visible_pillars = fields.Many2many(
        "sre.navigation.pillar",
        compute="_compute_sre_visible_pillars",
        help=(
            "Published and active SRE business pillars, used by the "
            "public top navigation. Ordered by sequence then name."
        ),
    )

    def _compute_sre_visible_pillars(self) -> None:
        Pillar = self.env["sre.navigation.pillar"]
        for website in self:
            website.sre_visible_pillars = Pillar.search([
                ("is_published", "=", True),
                ("active", "=", True),
            ], order="sequence, name")
