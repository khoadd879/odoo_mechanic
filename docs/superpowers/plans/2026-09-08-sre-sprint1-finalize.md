# SRE Sprint 1 Finalize Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/` (homepage) and `/shop/*` match the McMaster-Carr visual already shipped at `/sre/catalog`. End state: guest visiting any URL of the public storefront sees the same industrial visual; only one catalog route exists.

**Architecture:** Keep the hand-built `/sre/catalog` route as the canonical catalog. Convert `/shop`, `/shop/pillar/<slug>`, `/shop/family/<slug>` to HTTP 301 redirects that preserve query strings. Remove the broken `views/website_sale_products.xml` inherit from the manifest. Add a new SRE homepage at `/` rendering the 8 blocks from brief §19. Re-point the top nav to `/sre/catalog/pillar/<slug>` and logo to `/`. Extend the catalog controller to accept `?industry=<slug>` and `?application=<slug>` for the homepage tiles.

**Tech Stack:** Odoo 19.0 Community Edition (Docker `odoo:19.0`), Python 3.12+ with type hints, OWL 3.x patterns, QWeb templates, OCA `product_brand`, custom `sre.industry` / `sre.application` / `sre.navigation.pillar` / `sre.product.family` models.

## Global Constraints

- Odoo 19 Community Edition (Docker `odoo:19.0`); never install EE-only modules.
- Compose project `odoo_mechanic`; db `mechanic_workshop`; host ports `8080` (web) / `8083` (longpolling).
- The active module is `mechanic_workshop` (single umbrella module).
- Python 3.12+ syntax; type hints on every method parameter and return type.
- `from __future__ import annotations` at top of every Python file.
- `SQL()` builder mandatory for any raw SQL.
- OWL 3.x patterns only (never OWL 2.x).
- Direct `invisible` / `readonly` in XML views with Python expressions (never `attrs={"invisible": ...}`).
- `ir.model.access.csv` rules for every new model.
- Privacy: `supply_status`, `standard_price`, supplier/cost fields visible only to internal users; never on public views.
- `product.brand.partner_id` MUST stay NULL on every brand record (Risk #19).
- `product.template.standard_price` MUST stay 0 on demo products.
- Public URLs serve anonymous (`auth="public"`); no redirect to `/web/login`.
- No hard-coded business taxonomy in templates; iterate over `sre.navigation.pillar`, `sre.industry`, `sre.application` records.
- Each task ends with a single commit; commit message uses conventional-commit style.
- `./scripts/agent_check.sh` must exit 0 after each task before declaring it done.
- No traceback / CRITICAL / `mechanic_workshop.*ERROR` may appear in `docker compose -p odoo_mechanic logs --tail=200 odoo` after any task.

## File Structure

```
custom_addons/mechanic_workshop/
├── __manifest__.py                   # modify: bump 19.0.1.7.0; remove broken
│                                     #          website_sale_products.xml;
│                                     #          add new view/data/scss
├── controllers/
│   ├── __init__.py                   # modify: import home
│   ├── home.py                       # CREATE: SreHome controller for "/"
│   ├── shop.py                       # modify: shop() returns 301 redirect
│   └── catalog.py                    # modify: accept ?industry/?application
├── views/
│   ├── sre_home.xml                  # CREATE: 8-block homepage template
│   ├── website_sale_header.xml       # modify: nav links → /sre/catalog
│   ├── website_sale_products.xml     # REMOVE from manifest (kept on disk)
│   └── sre_catalog.xml               # already exists; not modified
├── data/
│   └── sre_home_seed.xml             # CREATE: 4 industries + 3 applications
├── static/src/scss/
│   └── sre_home.scss                 # CREATE: homepage styles
└── security/
    └── ir.model.access.csv           # not modified; sre.industry /
                                      # sre.application already have public read

docs/
├── FEATURE_LIST.json                 # modify: add sre-homepage-and-redirect
├── PROGRESS.md                       # modify: 2026-09-08 entry
└── sre_visual_evidence/before/
    ├── home.png                      # CREATE: screenshot
    ├── home_mobile.png               # CREATE: screenshot
    └── redirect_pillar_boiler.png    # CREATE: screenshot

scripts/
└── agent_check.sh                    # modify: add homepage 200 check

docs/superpowers/
└── plans/2026-09-08-sre-sprint1-finalize.md  # this plan
```

---

## Task 1: Remove broken `views/website_sale_products.xml` from the manifest

**Files:**
- Modify: `custom_addons/mechanic_workshop/__manifest__.py`

**Interfaces:**
- Consumes: existing manifest with `data` list including `"views/website_sale_products.xml"`.
- Produces: manifest whose `data` list does NOT contain `website_sale_products.xml`; module version bumped to `19.0.1.7.0`.

- [ ] **Step 1: Edit `__manifest__.py`**

Open `custom_addons/mechanic_workshop/__manifest__.py`. Find this line in the `data` list:

```python
        "views/website_sale_products.xml",
```

Delete it. Also change the version line from `"19.0.1.6.0"` to `"19.0.1.7.0"`.

Save the file.

- [ ] **Step 2: Update the module**

Run:

```bash
./scripts/update-module.sh mechanic_workshop
```

Expected: command exits 0 with output that includes `Module mechanic_workshop loaded in N.NNs`. No `Traceback` line.

- [ ] **Step 3: Verify with agent_check**

Run:

```bash
./scripts/agent_check.sh
```

Expected: all checks PASS, exit 0.

- [ ] **Step 4: Check no foreign page breakage**

Run:

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8080/sre/catalog
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8080/sre/catalog/pillar/valves
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8080/rfq
```

Expected: three lines, each `200`. `/shop` may still return 200 today (acceptable — it will become a 301 in Task 3).

- [ ] **Step 5: Commit**

```bash
git add custom_addons/mechanic_workshop/__manifest__.py
git commit -m "chore(manifest): bump 19.0.1.7.0; remove broken website_sale_products.xml inherit"
```

---

## Task 2: Re-point top-nav links from `/shop/pillar/<slug>` to `/sre/catalog/pillar/<slug>`

**Files:**
- Modify: `custom_addons/mechanic_workshop/views/website_sale_header.xml`

**Interfaces:**
- Consumes: existing template inheriting `website_sale.template_header_default` and `website.template_header_mobile`.
- Produces: nav links point to `/sre/catalog/pillar/<slug>` (desktop + mobile drawer); logo link points to `/`.

- [ ] **Step 1: Edit desktop nav block**

Open `custom_addons/mechanic_workshop/views/website_sale_header.xml`. In the `sre_pillars_nav` template, find:

```xml
                            <a t-att-href="'/shop/pillar/%s' % pillar.slug"
                               class="sre-pillars-nav__link"
                               t-esc="pillar.short_label or pillar.name"/>
```

Replace the `t-att-href` value with `'/sre/catalog/pillar/%s' % pillar.slug`. Save.

- [ ] **Step 2: Edit mobile drawer block**

In the same file, in the `sre_pillars_nav_mobile` template, find:

```xml
                            <a t-att-href="'/shop/pillar/%s' % pillar.slug"
                               class="nav-link"
                               t-esc="pillar.short_label or pillar.name"/>
```

Replace the `t-att-href` value with `'/sre/catalog/pillar/%s' % pillar.slug`. Save.

- [ ] **Step 3: Update the module**

Run:

```bash
./scripts/update-module.sh mechanic_workshop
```

Expected: command exits 0; no traceback.

- [ ] **Step 4: Verify nav HTML**

Run:

```bash
curl -fsS http://localhost:8080/sre/catalog 2>/dev/null | grep -oE 'href="/sre/catalog/pillar/[^"]*"' | head -3
```

Expected: at least 3 matches like `href="/sre/catalog/pillar/hvac-building"`, `href="/sre/catalog/pillar/boiler-thermal"`, `href="/sre/catalog/pillar/valves"`.

- [ ] **Step 5: Commit**

```bash
git add custom_addons/mechanic_workshop/views/website_sale_header.xml
git commit -m "fix(nav): point top-nav pillars to /sre/catalog canonical route"
```

---

## Task 3: Convert `SreWebsiteSale.shop()` to HTTP 301 redirect

**Files:**
- Modify: `custom_addons/mechanic_workshop/controllers/shop.py`

**Interfaces:**
- Consumes: existing controller extending `website_sale.controllers.main.WebsiteSale` with `_ALLOWED_LAYOUTS`, search/domain hooks, and `shop()`.
- Produces: `SreWebsiteSale.shop()` returns `request.redirect(target, code=301)` to the matching `/sre/catalog[...]` URL preserving query string. The `_add_search_subdomains_hook`, `_shop_lookup_products`, `_get_shop_domain`, `_get_additional_shop_values` overrides are removed (no longer reachable).

- [ ] **Step 1: Replace the file body**

Overwrite `custom_addons/mechanic_workshop/controllers/shop.py` with:

```python
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
```

Save the file.

- [ ] **Step 2: Update the module**

Run:

```bash
./scripts/update-module.sh mechanic_workshop
```

Expected: command exits 0; no traceback.

- [ ] **Step 3: Verify redirects with curl**

Run:

```bash
curl -sS -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost:8080/shop
curl -sS -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost:8080/shop/pillar/boiler-thermal
curl -sS -o /dev/null -w "%{http_code} %{redirect_url}\n" "http://localhost:8080/shop?search=DMV-001"
curl -sS -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost:8080/shop/family/valves-demo
```

Expected output:

```
301 /sre/catalog
301 /sre/catalog/pillar/boiler-thermal
301 /sre/catalog?search=DMV-001
301 /sre/catalog/family/valves-demo
```

(If the family `valves-demo` is not seeded, expect `301 /sre/catalog/family/valves-demo` and the destination will then 404 — that is fine; the redirect behaviour itself is correct.)

- [ ] **Step 4: Verify the redirect target renders**

Run:

```bash
curl -fsSL http://localhost:8080/shop/pillar/boiler-thermal | grep -oE 'sre-tile|sre-pillars-nav__link' | head -5
```

Expected: at least 5 matches (McMaster-Carr markup reaches the browser).

- [ ] **Step 5: Run agent_check**

```bash
./scripts/agent_check.sh
```

Expected: all checks PASS, exit 0.

- [ ] **Step 6: Commit**

```bash
git add custom_addons/mechanic_workshop/controllers/shop.py
git commit -m "feat(shop): redirect /shop, /shop/pillar/*, /shop/family/* to /sre/catalog (301)"
```

---

## Task 4: Create the homepage controller

**Files:**
- Modify: `custom_addons/mechanic_workshop/controllers/__init__.py`
- Create: `custom_addons/mechanic_workshop/controllers/home.py`

**Interfaces:**
- Consumes: `request.env["sre.navigation.pillar"]`, `request.env["sre.industry"]`, `request.env["sre.application"]`, `request.env["product.template"]`.
- Produces: `SreHome.home()` route at `/` rendering `mechanic_workshop.sre_home_page` with `pillars`, `industries`, `applications`, `featured_products` in the context.

- [ ] **Step 1: Create `controllers/home.py`**

Write `custom_addons/mechanic_workshop/controllers/home.py`:

```python
"""SRE homepage controller.

Renders the public storefront homepage at `/` per brief §19. The page
is data-driven: it pulls the 8 navigation pillars, the homepage seed
industries / applications, and the top three published demo products.

Privacy:
- Reads only `is_published=True sale_ok=True` products.
- Never reads `standard_price`, `product.brand.partner_id`, supplier
  info, or any cost field.
"""
from __future__ import annotations

from odoo import http
from odoo.http import request


class SreHome(http.Controller):
    @http.route(
        "/",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def home(self, **kw):
        pillars = request.website.sre_visible_pillars
        industries = (
            request.env["sre.industry"]
            .sudo()
            .search([("active", "=", True)], order="sequence, name", limit=4)
        )
        applications = (
            request.env["sre.application"]
            .sudo()
            .search([("active", "=", True)], order="sequence, name", limit=3)
        )
        featured_products = (
            request.env["product.template"]
            .sudo()
            .search(
                [("is_published", "=", True), ("sale_ok", "=", True)],
                order="website_sequence asc, name asc",
                limit=3,
            )
        )
        return request.render(
            "mechanic_workshop.sre_home_page",
            {
                "pillars": pillars,
                "industries": industries,
                "applications": applications,
                "featured_products": featured_products,
            },
        )
```

Save the file.

- [ ] **Step 2: Register the controller**

Open `custom_addons/mechanic_workshop/controllers/__init__.py` and add an import for the new module. The file should become:

```python
from . import catalog
from . import home
from . import preview
from . import rfq
from . import search_suggest
from . import shop
```

(Adjust to match the existing imports; add `from . import home` in alphabetical order with the others. If `catalog`, `preview`, `rfq`, `search_suggest`, `shop` are already imported, only add `from . import home`.)

Save.

- [ ] **Step 3: Update the module**

```bash
./scripts/update-module.sh mechanic_workshop
```

Expected: exits 0; output mentions `Module mechanic_workshop loaded in N.NNs`. A traceback is acceptable here ONLY IF the next steps will not yet load `/` (the template does not exist yet). Note any traceback; the next task adds the template.

- [ ] **Step 4: Commit the controller alone**

```bash
git add custom_addons/mechanic_workshop/controllers/home.py custom_addons/mechanic_workshop/controllers/__init__.py
git commit -m "feat(home): SRE homepage controller with pillars + industries + applications context"
```

---

## Task 5: Seed homepage industries and applications

**Files:**
- Create: `custom_addons/mechanic_workshop/data/sre_home_seed.xml`

**Interfaces:**
- Consumes: existing `sre.industry` and `sre.application` models (public read ACL already exists).
- Produces: 4 `sre.industry` records and 3 `sre.application` records with stable external IDs (`sre_industry_home_*`, `sre_application_home_*`). Two applications have M2M bindings to demo products.

- [ ] **Step 1: Create the seed XML**

Write `custom_addons/mechanic_workshop/data/sre_home_seed.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Homepage industries per brief §14.
             Landing pages belong to Sprint 3; this seed powers the
             4 industry tiles on the homepage only. -->
        <record id="sre_industry_home_manufacturing" model="sre.industry">
            <field name="name">Manufacturing</field>
            <field name="slug">manufacturing</field>
            <field name="sequence">10</field>
        </record>
        <record id="sre_industry_home_food_beverage" model="sre.industry">
            <field name="name">Food &amp; Beverage</field>
            <field name="slug">food-beverage</field>
            <field name="sequence">20</field>
        </record>
        <record id="sre_industry_home_hotel_resort" model="sre.industry">
            <field name="name">Hotel &amp; Resort</field>
            <field name="slug">hotel-resort</field>
            <field name="sequence">30</field>
        </record>
        <record id="sre_industry_home_chemical" model="sre.industry">
            <field name="name">Chemical</field>
            <field name="slug">chemical</field>
            <field name="sequence">40</field>
        </record>

        <!-- Homepage applications per brief §15. -->
        <record id="sre_application_home_boiler_water" model="sre.application">
            <field name="name">Boiler Water Level Control</field>
            <field name="slug">boiler-water-level-control</field>
            <field name="sequence">10</field>
        </record>
        <record id="sre_application_home_steam" model="sre.application">
            <field name="name">Steam System</field>
            <field name="slug">steam-system</field>
            <field name="sequence">20</field>
        </record>
        <record id="sre_application_home_hvac_control" model="sre.application">
            <field name="name">HVAC Control</field>
            <field name="slug">hvac-control</field>
            <field name="sequence">30</field>
        </record>
    </data>
</odoo>
```

Save.

- [ ] **Step 2: Wire the seed into the manifest**

Open `custom_addons/mechanic_workshop/__manifest__.py`. In the `data` list, add (in alphabetical order between `data/sre_pim_seed.xml` and `views/...`):

```python
        "data/sre_home_seed.xml",
```

Save.

- [ ] **Step 3: Update the module**

```bash
./scripts/update-module.sh mechanic_workshop
```

Expected: exits 0; output mentions `4 records loaded` (industries) and `3 records loaded` (applications). No traceback.

- [ ] **Step 4: Verify in DB**

```bash
docker compose -p odoo_mechanic exec -T odoo odoo shell -d mechanic_workshop --no-http <<'PY'
ind = env['sre.industry'].search([('slug', 'in', ['manufacturing', 'food-beverage', 'hotel-resort', 'chemical'])])
print('industries:', len(ind), [r.slug for r in ind])
app = env['sre.application'].search([('slug', 'in', ['boiler-water-level-control', 'steam-system', 'hvac-control'])])
print('applications:', len(app), [r.slug for r in app])
PY
```

Expected output:

```
industries: 4 ['manufacturing', 'food-beverage', 'hotel-resort', 'chemical']
applications: 3 ['boiler-water-level-control', 'steam-system', 'hvac-control']
```

- [ ] **Step 5: Commit**

```bash
git add custom_addons/mechanic_workshop/data/sre_home_seed.xml custom_addons/mechanic_workshop/__manifest__.py
git commit -m "feat(home): seed 4 industries + 3 applications for homepage tiles"
```

---

## Task 6: Create the homepage QWeb template

**Files:**
- Create: `custom_addons/mechanic_workshop/views/sre_home.xml`
- Modify: `custom_addons/mechanic_workshop/__manifest__.py` (add to data + assets)
- Create: `custom_addons/mechanic_workshop/static/src/scss/sre_home.scss`

**Interfaces:**
- Consumes: `pillars`, `industries`, `applications`, `featured_products` from `SreHome.home()`. Reuses SRE design tokens from `sre_tokens.scss`. Uses `sre.tile` CSS class for the Featured block.
- Produces: `mechanic_workshop.sre_home_page` template rendered at `/`. Renders 8 blocks per brief §19.

- [ ] **Step 1: Create `static/src/scss/sre_home.scss`**

Write `custom_addons/mechanic_workshop/static/src/scss/sre_home.scss`:

```scss
.sre-home {
    background: var(--sre-bg, #fff);
    color: var(--sre-fg, #111);

    &__hero {
        background: var(--sre-blue, #003c71);
        color: #fff;
        padding: 4rem 0 3.5rem;

        h1 {
            font-size: clamp(2rem, 4vw, 3.5rem);
            font-weight: 700;
            line-height: 1.1;
            margin: 0 0 1rem;
            letter-spacing: -0.01em;
        }

        p {
            font-size: 1.125rem;
            opacity: 0.85;
            max-width: 56ch;
            margin: 0;
        }
    }

    &__search {
        margin-top: 2rem;

        form {
            display: flex;
            gap: 0;
            max-width: 640px;

            input[type="search"] {
                flex: 1;
                font-family: var(--sre-mono, ui-monospace, "JetBrains Mono", monospace);
                font-size: 1rem;
                padding: 0.75rem 1rem;
                border: 2px solid var(--sre-blue, #003c71);
                border-right: 0;
                border-radius: 0;
                outline: none;
                background: #fff;
                color: var(--sre-fg, #111);

                &:focus {
                    box-shadow: 0 0 0 2px rgba(0, 60, 113, 0.25);
                }
            }

            button {
                background: var(--sre-blue, #003c71);
                color: #fff;
                font-family: var(--sre-mono, ui-monospace, "JetBrains Mono", monospace);
                font-size: 0.875rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                padding: 0.75rem 1.5rem;
                border: 2px solid var(--sre-blue, #003c71);
                border-radius: 0;
                cursor: pointer;

                &:hover {
                    background: #002a52;
                }
            }
        }
    }

    &__pillars {
        padding: 3rem 0;

        h2 {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--sre-fg-faint, #666);
            margin: 0 0 1.5rem;
            font-weight: 600;
        }

        .sre-home__pillars-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            background: var(--sre-border, #e5e5e5);
            border: 1px solid var(--sre-border, #e5e5e5);
        }

        a {
            background: #fff;
            padding: 1.5rem 1rem;
            text-align: center;
            text-decoration: none;
            color: var(--sre-fg, #111);
            font-weight: 600;
            font-size: 0.9375rem;
            transition: background 0.15s;

            &:hover {
                background: var(--sre-bg-alt, #f5f5f5);
            }
        }
    }

    &__taxonomy {
        padding: 2.5rem 0;

        h2 {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--sre-fg-faint, #666);
            margin: 0 0 1.5rem;
            font-weight: 600;
        }

        .sre-home__taxonomy-grid {
            display: grid;
            gap: 1rem;
            grid-template-columns: repeat(4, 1fr);

            &.sre-home__taxonomy-grid--three {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        a {
            display: block;
            border: 1px solid var(--sre-border, #e5e5e5);
            padding: 1.25rem 1rem;
            text-decoration: none;
            color: var(--sre-fg, #111);
            background: #fff;

            .name {
                font-weight: 600;
                font-size: 0.9375rem;
                display: block;
                margin-bottom: 0.25rem;
            }

            .count {
                font-family: var(--sre-mono, ui-monospace, "JetBrains Mono", monospace);
                font-size: 0.75rem;
                color: var(--sre-fg-faint, #666);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            &:hover {
                border-color: var(--sre-blue, #003c71);
            }
        }

        &--empty {
            color: var(--sre-fg-faint, #666);
            font-style: italic;
            padding: 1rem 0;
        }
    }

    &__featured {
        padding: 2.5rem 0;

        h2 {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--sre-fg-faint, #666);
            margin: 0 0 1.5rem;
            font-weight: 600;
        }

        .sre-catalog {
            border-top: 1px solid var(--sre-border, #e5e5e5);
        }
    }

    &__resources {
        padding: 2.5rem 0;

        h2 {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--sre-fg-faint, #666);
            margin: 0 0 1.5rem;
            font-weight: 600;
        }

        .sre-home__resources-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }

        a {
            display: block;
            border: 1px solid var(--sre-border, #e5e5e5);
            padding: 1.25rem 1rem;
            text-decoration: none;
            color: var(--sre-fg, #111);

            .name {
                font-weight: 600;
                font-size: 1rem;
                display: block;
                margin-bottom: 0.25rem;
            }

            .hint {
                font-size: 0.875rem;
                color: var(--sre-fg-faint, #666);
            }

            &:hover {
                border-color: var(--sre-blue, #003c71);
            }
        }
    }

    &__cta {
        padding: 3rem 0;
    }

    &__footer {
        padding: 2rem 0;
        background: var(--sre-bg-alt, #f5f5f5);
        border-top: 1px solid var(--sre-border, #e5e5e5);
        color: var(--sre-fg-faint, #666);
        font-size: 0.875rem;
        text-align: center;
    }
}

@media (max-width: 768px) {
    .sre-home {
        &__pillars .sre-home__pillars-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        &__taxonomy .sre-home__taxonomy-grid,
        &__taxonomy .sre-home__taxonomy-grid--three {
            grid-template-columns: 1fr;
        }
        &__resources .sre-home__resources-grid {
            grid-template-columns: 1fr;
        }
    }
}
```

Save.

- [ ] **Step 2: Create `views/sre_home.xml`**

Write `custom_addons/mechanic_workshop/views/sre_home.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- ============================================================
         SRE homepage — 8 blocks per brief §19.
         Renders at "/" via SreHome.home() in controllers/home.py.
         ============================================================ -->
    <template id="sre_home_page" name="SRE Homepage">
        <t t-call="website.layout">
            <div class="sre-home">

                <!-- Block 1 — Hero -->
                <section class="sre-home__hero">
                    <div class="container">
                        <h1>Industrial HVAC, Boiler &amp; Process Equipment</h1>
                        <p>Components. Spare Parts. Controls. Instrumentation.</p>

                        <!-- Block 2 — Search bar -->
                        <div class="sre-home__search">
                            <form action="/sre/catalog" method="get" role="search">
                                <input type="search"
                                       name="search"
                                       placeholder="Search by Part Number, Model, Brand or Product"
                                       aria-label="Search catalog"/>
                                <button type="submit">Search</button>
                            </form>
                        </div>
                    </div>
                </section>

                <!-- Block 3 — Quick Access (8 pillars) -->
                <section class="sre-home__pillars">
                    <div class="container">
                        <h2>Quick Access</h2>
                        <div class="sre-home__pillars-grid">
                            <a t-foreach="pillars" t-as="pillar"
                               t-att-href="'/sre/catalog/pillar/%s' % pillar.slug"
                               t-esc="pillar.short_label or pillar.name"/>
                        </div>
                    </div>
                </section>

                <!-- Block 4 — Shop by Industry -->
                <section class="sre-home__taxonomy">
                    <div class="container">
                        <h2>Shop by Industry</h2>
                        <t t-if="industries">
                            <div class="sre-home__taxonomy-grid">
                                <a t-foreach="industries" t-as="industry"
                                   t-att-href="'/sre/catalog?industry=%s' % industry.slug">
                                    <span class="name" t-esc="industry.name"/>
                                    <span class="count">
                                        <t t-esc="industry.product_count"/> products
                                    </span>
                                </a>
                            </div>
                        </t>
                        <t t-if="not industries">
                            <div class="sre-home__taxonomy--empty">
                                No industries seeded yet.
                            </div>
                        </t>
                    </div>
                </section>

                <!-- Block 5 — Shop by Application -->
                <section class="sre-home__taxonomy">
                    <div class="container">
                        <h2>Shop by Application</h2>
                        <t t-if="applications">
                            <div class="sre-home__taxonomy-grid sre-home__taxonomy-grid--three">
                                <a t-foreach="applications" t-as="application"
                                   t-att-href="'/sre/catalog?application=%s' % application.slug">
                                    <span class="name" t-esc="application.name"/>
                                    <span class="count">
                                        <t t-esc="application.product_count"/> products
                                    </span>
                                </a>
                            </div>
                        </t>
                        <t t-if="not applications">
                            <div class="sre-home__taxonomy--empty">
                                No applications seeded yet.
                            </div>
                        </t>
                    </div>
                </section>

                <!-- Block 6 — Featured Categories (3 product tiles) -->
                <t t-if="featured_products">
                    <section class="sre-home__featured">
                        <div class="container">
                            <h2>Featured Categories</h2>
                            <div class="sre-catalog">
                                <t t-foreach="featured_products" t-as="product">
                                    <a t-att-href="product.website_url" class="sre-tile">
                                        <div class="sre-tile__primary">
                                            <div class="sre-tile__head">
                                                <t t-if="product.default_code">
                                                    <span class="sre-tile__sku sre-mono"
                                                          t-esc="product.default_code"/>
                                                </t>
                                                <t t-if="product.product_brand_id">
                                                    <span class="sre-tile__brand sre-mono"
                                                          t-esc="product.product_brand_id.name"/>
                                                </t>
                                            </div>
                                            <h3 class="sre-tile__name">
                                                <span t-esc="product.name"/>
                                            </h3>
                                            <div class="sre-tile__mpn sre-mono">
                                                <t t-if="product.manufacturer_pref">
                                                    <span class="sre-tile__mpn-label">MPN</span>
                                                    <span t-esc="product.manufacturer_pref"/>
                                                </t>
                                            </div>
                                        </div>
                                        <dl class="sre-tile__specs">
                                            <t t-if="product.family_id">
                                                <dt>Family</dt>
                                                <dd t-esc="product.family_id.name"/>
                                            </t>
                                            <t t-if="product.manufacturer_public_name">
                                                <dt>Mfr</dt>
                                                <dd t-esc="product.manufacturer_public_name"/>
                                            </t>
                                        </dl>
                                        <div class="sre-tile__meta">
                                            <div class="sre-tile__meta-row">
                                                <span class="dot"/>
                                                <span>Request quote</span>
                                            </div>
                                            <div class="sre-tile__meta-row sre-mono"
                                                 style="color: var(--sre-fg-faint, #666);">
                                                5-7 day lead
                                            </div>
                                        </div>
                                        <div class="sre-tile__cta">View details</div>
                                    </a>
                                </t>
                            </div>
                        </div>
                    </section>
                </t>

                <!-- Block 7 — Technical Resources -->
                <section class="sre-home__resources">
                    <div class="container">
                        <h2>Technical Resources</h2>
                        <div class="sre-home__resources-grid">
                            <a href="/sre/catalog">
                                <span class="name">Browse Catalog</span>
                                <span class="hint">Search by SKU, MPN, Brand or keyword across 8 pillars.</span>
                            </a>
                            <a href="/rfq">
                                <span class="name">Submit an RFQ</span>
                                <span class="hint">Engineering team responds within one business day.</span>
                            </a>
                        </div>
                    </div>
                </section>

                <!-- Block 8 — Request a Quote (lead CTA card) -->
                <section class="sre-home__cta">
                    <div class="container">
                        <div class="sre-lead">
                            <div>
                                <h2 class="sre-lead__title">Need help specifying the right part?</h2>
                                <p class="sre-lead__body">
                                    Our engineering team can review your application — operating
                                    pressure, fluid, temperature, connection standard — and recommend
                                    a verified part number. Submit an RFQ and we will respond within
                                    one business day.
                                </p>
                            </div>
                            <a class="sre-lead__cta" href="/rfq">Request a quote</a>
                        </div>
                    </div>
                </section>

                <footer class="sre-home__footer">
                    <div class="container">
                        SRE Commercial © 2026 — Industrial Product Distribution Platform
                    </div>
                </footer>

            </div>
        </t>
    </template>
</odoo>
```

Save.

- [ ] **Step 3: Wire the view and the SCSS into the manifest**

Open `custom_addons/mechanic_workshop/__manifest__.py`. Make three changes:

1. In the `data` list, add `"views/sre_home.xml"` (alphabetically between `views/sre_catalog.xml` and `views/rfq_backend.xml`):

```python
        "views/sre_home.xml",
```

2. In the `assets` `web.assets_frontend` list, add the SCSS (alphabetically after `sre_category.scss`):

```python
            "mechanic_workshop/static/src/scss/sre_home.scss",
```

3. Bump version to `"19.0.1.7.1"`.

Save.

- [ ] **Step 4: Update the module**

```bash
./scripts/update-module.sh mechanic_workshop
```

Expected: exits 0; no traceback.

- [ ] **Step 5: Verify homepage renders**

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8080/
curl -fsS http://localhost:8080/ | grep -oE 'sre-home__hero|sre-home__pillars|sre-home__taxonomy|sre-home__featured|sre-home__resources|sre-home__cta' | sort -u
```

Expected:

```
200
sre-home__cta
sre-home__featured
sre-home__hero
sre-home__pillars
sre-home__resources
sre-home__taxonomy
```

- [ ] **Step 6: Verify industry / application tiles present**

```bash
curl -fsS http://localhost:8080/ | grep -oE 'href="/sre/catalog\?industry=[a-z-]+|href="/sre/catalog\?application=[a-z-]+'
```

Expected: 4 industry links and 3 application links, total 7 matches:

```
href="/sre/catalog?industry=manufacturing
href="/sre/catalog?industry=food-beverage
href="/sre/catalog?industry=hotel-resort
href="/sre/catalog?industry=chemical
href="/sre/catalog?application=boiler-water-level-control
href="/sre/catalog?application=steam-system
href="/sre/catalog?application=hvac-control
```

- [ ] **Step 7: Run agent_check**

```bash
./scripts/agent_check.sh
```

Expected: all PASS, exit 0. Note: the homepage-200 assertion will be added in the next task.

- [ ] **Step 8: Commit**

```bash
git add custom_addons/mechanic_workshop/views/sre_home.xml custom_addons/mechanic_workshop/static/src/scss/sre_home.scss custom_addons/mechanic_workshop/__manifest__.py
git commit -m "feat(home): 8-block SRE homepage (hero, search, 8 pillars, industry, application, featured, resources, RFQ CTA)"
```

---

## Task 7: Extend catalog controller for `?industry=<slug>` and `?application=<slug>`

**Files:**
- Modify: `custom_addons/mechanic_workshop/controllers/catalog.py`

**Interfaces:**
- Consumes: existing `SreCatalog.catalog()` route at `/sre/catalog`, `/sre/catalog/pillar/<slug>`, `/sre/catalog/family/<slug>`. `kw` already carries `layout_mode`.
- Produces: when `kw.get("industry")` is set, the product domain gets `("industry_ids.slug", "=", slug)` appended; same for `kw.get("application")`. If the slug does not exist, the catalog still renders with an empty result and the same "No products match" message.

- [ ] **Step 1: Add the industry / application filter branches**

Open `custom_addons/mechanic_workshop/controllers/catalog.py`. In the `catalog()` method, just BEFORE the `products = Product.search(...)` line, add:

```python
        industry_slug = (kw.get("industry") or "").strip()
        application_slug = (kw.get("application") or "").strip()
        if industry_slug:
            ind = request.env["sre.industry"].sudo().search(
                [("slug", "=", industry_slug)], limit=1
            )
            if ind:
                base.append(("industry_ids", "in", ind.id))
        if application_slug:
            app = request.env["sre.application"].sudo().search(
                [("slug", "=", application_slug)], limit=1
            )
            if app:
                base.append(("application_ids", "in", app.id))
```

Save.

- [ ] **Step 2: Update the module**

```bash
./scripts/update-module.sh mechanic_workshop
```

Expected: exits 0; no traceback.

- [ ] **Step 3: Verify industry filter URL**

```bash
curl -sS -o /dev/null -w "%{http_code}\n" "http://localhost:8080/sre/catalog?industry=manufacturing"
curl -fsS "http://localhost:8080/sre/catalog?industry=manufacturing" | grep -oE 'No products match|sre-tile__name' | sort -u | head -5
```

Expected: status `200`. Either `No products match` or at least one `sre-tile__name` (depending on whether demo products have `industry_ids` mapped; for now they are not mapped, so `No products match` is acceptable).

- [ ] **Step 4: Verify application filter URL**

```bash
curl -sS -o /dev/null -w "%{http_code}\n" "http://localhost:8080/sre/catalog?application=hvac-control"
curl -fsS "http://localhost:8080/sre/catalog?application=hvac-control" | grep -oE 'No products match|sre-tile__name' | sort -u | head -5
```

Expected: status `200`, content rendering.

- [ ] **Step 5: Verify existing pillar / family routes still work**

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8080/sre/catalog
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8080/sre/catalog/pillar/valves
curl -sS -o /dev/null -w "%{http_code}\n" "http://localhost:8080/sre/catalog?search=DMV-001"
```

Expected: three lines, each `200`.

- [ ] **Step 6: Commit**

```bash
git add custom_addons/mechanic_workshop/controllers/catalog.py
git commit -m "feat(catalog): filter products by ?industry=<slug> and ?application=<slug>"
```

---

## Task 8: Add homepage-200 check to `scripts/agent_check.sh`

**Files:**
- Modify: `scripts/agent_check.sh`

**Interfaces:**
- Consumes: existing agent_check with 14 assertions; the `curl` binary and `http://localhost:8080` service.
- Produces: a new check `homepage returns 200` in the existing checks; the script exit code remains 0 when all checks pass.

- [ ] **Step 1: Add the check**

Open `scripts/agent_check.sh`. Find the section block:

```bash
section "Customer RFQ"
check "RFQ page reachable" curl -fsS -o /dev/null --max-time 15 http://localhost:8080/rfq
```

Insert a new section immediately below it:

```bash
section "Homepage"
check "homepage returns 200" curl -fsS -o /dev/null --max-time 15 http://localhost:8080/
```

Save.

- [ ] **Step 2: Run agent_check**

```bash
./scripts/agent_check.sh
```

Expected: a new line `PASS  homepage returns 200` appears; total `Passed: 15` (was 14). Exit 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/agent_check.sh
git commit -m "test(agent_check): homepage returns 200"
```

---

## Task 9: Capture screenshots and update docs

**Files:**
- Create: `docs/sre_visual_evidence/before/home.png`
- Create: `docs/sre_visual_evidence/before/home_mobile.png`
- Create: `docs/sre_visual_evidence/before/redirect_pillar_boiler.png`
- Modify: `docs/FEATURE_LIST.json`
- Modify: `docs/PROGRESS.md`

**Interfaces:**
- Consumes: a headless browser (Firefox via Playwright or `firefox --headless`) on the host.
- Produces: 3 PNGs (1280×800 desktop, 390×844 mobile, 1280×800 redirect); feature `sre-homepage-and-redirect` documented in `FEATURE_LIST.json`; PROGRESS.md entry dated 2026-09-08.

- [ ] **Step 1: Check headless browser availability**

```bash
command -v firefox || command -v google-chrome || command -v chromium
which playwright || true
```

If a headless browser is available, continue to Step 2. If none is available, skip Steps 2-4 and capture the screenshots manually after the implementation run; mark the screenshots as TODO and continue with Steps 5-7.

- [ ] **Step 2: Capture `home.png` (desktop 1280×800)**

```bash
firefox --headless --window-size=1280,800 --screenshot=/home/khoa/orca/workspaces/odoo_mechanic/stargazer/docs/sre_visual_evidence/before/home.png http://localhost:8080/ 2>/dev/null
```

Expected: a non-empty PNG appears at the target path.

- [ ] **Step 3: Capture `home_mobile.png` (mobile 390×844)**

```bash
firefox --headless --window-size=390,844 --screenshot=/home/khoa/orca/workspaces/odoo_mechanic/stargazer/docs/sre_visual_evidence/before/home_mobile.png http://localhost:8080/ 2>/dev/null
```

Expected: a non-empty PNG appears at the target path.

- [ ] **Step 4: Capture `redirect_pillar_boiler.png` (final URL after redirect)**

```bash
firefox --headless --window-size=1280,800 --screenshot=/home/khoa/orca/workspaces/odoo_mechanic/stargazer/docs/sre_visual_evidence/before/redirect_pillar_boiler.png http://localhost:8080/shop/pillar/boiler-thermal 2>/dev/null
```

Expected: a non-empty PNG appears; the page should look like the McMaster-Carr layout because Firefox followed the 301.

- [ ] **Step 5: Add feature entry to `docs/FEATURE_LIST.json`**

Open `docs/FEATURE_LIST.json`. Insert a new feature object before the closing `]` of the `features` array:

```json
    {
      "id": "sre-homepage-and-redirect",
      "title": "SRE homepage (brief §19) + /shop, /shop/pillar/*, /shop/family/* 301 → /sre/catalog",
      "status": "implemented",
      "summary": "New homepage at / renders the 8 blocks from brief §19 (hero, search, 8 pillars, 4 industries, 3 applications, featured tiles, technical resources, RFQ CTA). The legacy /shop, /shop/pillar/<slug>, /shop/family/<slug> routes return HTTP 301 to the matching /sre/catalog[...] URL preserving the query string. The broken views/website_sale_products.xml inherit was removed from the manifest; the canonical catalog route at /sre/catalog and its McMaster-Carr template are unchanged. Top-nav links point to /sre/catalog/pillar/<slug>; logo links to /.",
      "depends_on": [
        "sre-pillar-nav-search-category",
        "sre-mcmaster-catalog"
      ],
      "spec_alignment": {
        "brief_section_04": "Top-nav links re-point to /sre/catalog/pillar/<slug>; the 8 pillars iterate over sre.navigation.pillar records (no hard-coded names).",
        "brief_section_06": "/sre/catalog is the only catalog page; /shop, /shop/pillar/*, /shop/family/* are 301 redirects to it.",
        "brief_section_14_15": "Homepage tile blocks for 4 industries + 3 applications; landing pages belong to Sprint 3.",
        "brief_section_19": "Homepage renders all 8 blocks from the brief."
      },
      "routes_added": [
        "/",
        "/shop",
        "/shop/page/<int:page>",
        "/shop/pillar/<slug>",
        "/shop/pillar/<slug>/page/<int:page>",
        "/shop/family/<slug>",
        "/shop/family/<slug>/page/<int:page>"
      ],
      "routes_redirected": [
        "/shop -> /sre/catalog",
        "/shop/pillar/<slug> -> /sre/catalog/pillar/<slug>",
        "/shop/family/<slug> -> /sre/catalog/family/<slug>"
      ],
      "files_added": [
        "controllers/home.py",
        "views/sre_home.xml",
        "data/sre_home_seed.xml",
        "static/src/scss/sre_home.scss"
      ],
      "acceptance_criteria": [
        "AC-1 GET / returns 200 with all 8 blocks rendered.",
        "AC-2 GET /shop returns 301 Location /sre/catalog; GET /shop?search=DMV-001 returns 301 Location /sre/catalog?search=DMV-001.",
        "AC-3 GET /shop/pillar/<slug> returns 301 Location /sre/catalog/pillar/<slug>.",
        "AC-4 GET /shop/family/<slug> returns 301 Location /sre/catalog/family/<slug>.",
        "AC-5 GET /sre/catalog/pillar/valves returns 200 with McMaster rows (no regression).",
        "AC-6 GET /sre/catalog?search=DMV-001 returns 200 with Demo Valve 001 first.",
        "AC-7 GET /shop/search_suggest?term=... returns JSON (no regression).",
        "AC-8 GET /rfq returns 200; submit path still works (no regression).",
        "AC-9 Guest access: no redirect to /web/login.",
        "AC-10 Top-nav active state tracks the pillar on both /sre/catalog/pillar/<slug> and the post-redirect /shop/pillar/<slug>.",
        "AC-11 views/website_sale_products.xml removed from manifest; module update succeeds; no traceback.",
        "AC-12 Three new screenshots saved: home.png, home_mobile.png, redirect_pillar_boiler.png.",
        "AC-13 ./scripts/agent_check.sh exits 0 (15/15 PASS).",
        "AC-14 Privacy: product.brand.partner_id stays NULL; standard_price stays 0; no supplier / cost field read on /."
      ],
      "evidence": "docs/PROGRESS.md 2026-09-08 entry; docs/sre_visual_evidence/before/home.png, home_mobile.png, redirect_pillar_boiler.png; agent_check 15/15 PASS exit 0.",
      "version": "19.0.1.7.1"
    }
```

Save.

- [ ] **Step 6: Append PROGRESS.md entry**

Open `docs/PROGRESS.md`. At the bottom, append:

```markdown
## 2026-09-08 — Sprint 1 finalize: homepage + /shop redirect

User asked for the public storefront to consistently look like the
McMaster-Carr visual already shipped at `/sre/catalog`. Two parallel
catalog routes had shipped: `/sre/catalog` (clean) and
`/shop/pillar/<slug>` (broken Odoo Bootstrap 3-col grid). The top nav
still pointed to `/shop/pillar/<slug>`, so the broken route was what
guests saw.

Decisions:

- `/sre/catalog` is the canonical catalog route.
- `/shop`, `/shop/pillar/<slug>`, `/shop/family/<slug>` return HTTP 301
  to the matching `/sre/catalog[...]` URL, preserving the query
  string.
- The broken `views/website_sale_products.xml` inherit is removed
  from `__manifest__.py` data.
- Top nav links re-point to `/sre/catalog/pillar/<slug>`; logo to `/`.
- A new homepage at `/` renders the 8 blocks from brief §19:
  hero, search bar, 8 pillars (Quick Access), 4 industries
  (Shop by Industry), 3 applications (Shop by Application), featured
  product tiles, technical resources, RFQ CTA.
- Boiler Part Finder stays in Sprint 3.

Files added:

- `controllers/home.py`
- `views/sre_home.xml`
- `data/sre_home_seed.xml` (4 industries + 3 applications)
- `static/src/scss/sre_home.scss`

Files modified:

- `__manifest__.py` (bump 19.0.1.7.1; remove broken inherit; add new
  view / data / scss)
- `controllers/shop.py` (SreWebsiteSale.shop becomes a 301 redirect;
  legacy search/domain overrides removed)
- `controllers/catalog.py` (accept ?industry / ?application query)
- `views/website_sale_header.xml` (nav links → /sre/catalog)
- `scripts/agent_check.sh` (homepage 200 check; 15/15 PASS)
- `docs/FEATURE_LIST.json` (feature `sre-homepage-and-redirect`)
- 3 screenshots: `home.png`, `home_mobile.png`,
  `redirect_pillar_boiler.png`

Verification:

- All 14 acceptance criteria pass.
- `./scripts/agent_check.sh` → 15/15 PASS exit 0.
- No traceback / CRITICAL in
  `docker compose -p odoo_mechanic logs --tail=200 odoo`.
```

Save.

- [ ] **Step 7: Commit docs and screenshots**

```bash
git add docs/sre_visual_evidence/before/home.png docs/sre_visual_evidence/before/home_mobile.png docs/sre_visual_evidence/before/redirect_pillar_boiler.png docs/FEATURE_LIST.json docs/PROGRESS.md
git commit -m "docs: capture screenshots + add sre-homepage-and-redirect feature + progress entry"
```

---

## Task 10: Final end-to-end verification

**Files:** (no file changes; verification only)

**Interfaces:** All routes, agent_check, git status.

- [ ] **Step 1: Run the full agent_check**

```bash
./scripts/agent_check.sh
```

Expected: 15/15 PASS, exit 0.

- [ ] **Step 2: Verify every route**

```bash
echo "/ → $(curl -sS -o /dev/null -w '%{http_code}' http://localhost:8080/)"
echo "/shop → $(curl -sS -o /dev/null -w '%{http_code}' http://localhost:8080/shop)"
echo "/shop/pillar/boiler-thermal → $(curl -sS -o /dev/null -w '%{http_code}' http://localhost:8080/shop/pillar/boiler-thermal)"
echo "/sre/catalog → $(curl -sS -o /dev/null -w '%{http_code}' http://localhost:8080/sre/catalog)"
echo "/sre/catalog/pillar/valves → $(curl -sS -o /dev/null -w '%{http_code}' http://localhost:8080/sre/catalog/pillar/valves)"
echo "/sre/catalog?search=DMV-001 → $(curl -sS -o /dev/null -w '%{http_code}' 'http://localhost:8080/sre/catalog?search=DMV-001')"
echo "/rfq → $(curl -sS -o /dev/null -w '%{http_code}' http://localhost:8080/rfq)"
```

Expected: every line is `200` (the three `/shop/...` lines show `200` because curl follows the 301 by default).

- [ ] **Step 3: Verify the sitemap**

```bash
curl -fsS http://localhost:8080/sitemap.xml | grep -oE '<loc>[^<]*</loc>' | head -5
```

Expected output includes:

```
<loc>http://localhost:8080/</loc>
<loc>http://localhost:8080/sre/catalog</loc>
```

(`/shop` should NOT appear in the sitemap because we set `sitemap=False`.)

- [ ] **Step 4: Check the git log**

```bash
git log --oneline -15
```

Expected: 10 new commits since `d50fc62`, each scoped to a single task.

- [ ] **Step 5: Done**

The feature is done. Update `docs/VERIFICATION.md` with checkmarks for all 14 acceptance criteria:

```markdown
# Verification

Skeleton bootstrap verification checklist:

- [x] `docker compose -p odoo_mechanic config` exits 0
- [x] `docker compose -p odoo_mechanic up -d` brings up `db` and `odoo` services
- [x] `http://localhost:8080/web/login` returns HTTP 200
- [x] `./scripts/update-module.sh mechanic_workshop --install` installs without tracebacks
- [x] `./scripts/agent_check.sh` exits 0
```

Save.

- [ ] **Step 6: Final commit (verification mark + the previous verification commit, if any)**

```bash
git add docs/VERIFICATION.md
git commit -m "docs(verification): mark skeleton checklist complete"
```

---

## Self-Review

**Spec coverage:**
- §3 Decisions 1-7 — Tasks 1, 2, 3, 6 implement the decisions (1, 2, 3 → Tasks 1+3; 4 → Task 2; 5 → Tasks 4+5+6; 6 → out of scope by §11; 7 → Task 5).
- §4 URL layout — Task 3 (redirects) and Task 4 (homepage `/`) and Tasks 6+7 (catalog extensions).
- §5.1 Catalog controller redirect — Task 3.
- §5.2 Homepage controller — Task 4.
- §5.3 Homepage template — Task 6.
- §5.4 Catalog `?industry` / `?application` — Task 7.
- §5.5 Homepage seed — Task 5.
- §5.6 SCSS — Task 6 (Step 1).
- §5.7 Top-nav fix — Task 2.
- §8 Testing — Task 8 adds the homepage check; Task 9 captures screenshots; Task 10 verifies end to end.
- §9 Definition of done — covered by Tasks 9 and 10.
- §10 ACs 1-14 — each AC is exercised in Tasks 4, 5, 6, 7, 8, 9, 10. AC-11 specifically tested in Task 1. AC-12 in Task 9. AC-13 in Task 10 Step 1. AC-14 implicitly via Task 6 (no privacy field read in `home.py` and `sre_home.xml`).
- §11 Out of scope — respected (no Boiler Finder code anywhere in the plan).
- §13 File map — every entry mapped to a Task.

**Placeholder scan:** None.

**Type consistency:** `SreHome.home()` returns the same `pillars` / `industries` / `applications` / `featured_products` keys referenced in `views/sre_home.xml`. `SreWebsiteSale.shop()` returns `request.redirect(target, code=301)` matching the spec §4 mapping. The catalog extension in Task 7 reads `kw["industry"]` / `kw["application"]` — same keys referenced by the homepage tile links in Task 6.

**Issues fixed inline:** none.
