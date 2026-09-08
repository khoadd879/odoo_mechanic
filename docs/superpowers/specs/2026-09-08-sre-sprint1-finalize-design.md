# SRE Sprint 1 Finalize — Canonical catalog route + Homepage + /shop redirect

**Status:** Approved (brainstorming session 2026-09-08)
**Date:** 2026-09-08
**Author:** Brainstorming session with user
**Odoo version:** 19.0 Community Edition
**Source brief:** `docs/SRE Commercial Website Transformation Brief.docx.md`
**Source spec:** `docs/superpowers/specs/2026-09-07-sre-commercial-design.md`
**Scope:** Sprint 1 finalization (visual + URL consistency + homepage)
**Sprint scope:** Full Sprint 1 per `2026-09-07-sre-sprint1-foundation.md`,
plus the homepage from brief §19. Boiler Part Finder stays in Sprint 3.

## 1. Goal

Close the gap between the McMaster-Carr visual that was hand-built at
`/sre/catalog` and the broken Odoo Bootstrap 3-column grid that the user
still sees at `/shop/pillar/boiler-thermal`. Make `/` (homepage)
match brief §19. End state: a guest visiting any URL of the public
storefront sees the same industrial visual; only one catalog route
exists; the brief's eight homepage blocks are present.

## 2. Why the gap exists today

Two parallel catalog routes shipped during the visual refresh:

- `/sre/catalog`, `/sre/catalog/pillar/<slug>`, `/sre/catalog/family/<slug>`
  rendered by `controllers/catalog.py` + `views/sre_catalog.xml`. This is
  the McMaster-Carr row layout verified by
  `docs/sre_visual_evidence/before/sre_catalog.png` (7 demo products,
  single-column rows, monospace SKU/MPN, view-mode toggle, lead CTA).
- `/shop`, `/shop/pillar/<slug>`, `/shop/family/<slug>` rendered by
  the Odoo 19 native `website_sale.products` template with the
  `views/website_sale_products.xml` inherit applied on top. The PROGRESS
  entry on 2026-09-08 already records that this inherit "is left
  disabled" because Odoo 19's strict QWeb `t-elif` parser refused to
  render it once extra conditional blocks were added. The result is the
  broken 3-column card grid in the user's screenshot.

The top nav (`views/website_sale_header.xml`) still links to
`/shop/pillar/<slug>`, so the broken route is what the user sees. The
canonical route at `/sre/catalog` is unreachable from the nav.

There is no homepage yet; `/` falls back to the Odoo default page.

## 3. Decisions

1. **`/sre/catalog` is the canonical catalog route.** Keep it; do not
   rewrite it.
2. **`/shop`, `/shop/pillar/<slug>`, `/shop/family/<slug>` return HTTP
   301** to the matching `/sre/catalog[...]` URL, preserving the
   query string (`?search=...&attrib=...&order=...&ppg=...`).
3. **The broken `views/website_sale_products.xml` inherit is removed
   from `__manifest__.py` data.** Other inherits (`sre_products_item_inherit`,
   `sre_product_detail_inherit`) stay; they do not depend on the broken
   file and they are exercised by `/shop/<product>` which is unchanged.
4. **The top nav links point to `/sre/catalog/pillar/<slug>`.** Logo
   links to `/`. The active-pillar state still reads from the URL slug.
5. **A new SRE homepage renders at `/`** with the eight blocks from
   brief §19, using the same SRE design tokens (industrial blue,
   monospace identifiers, no border-radius, dense rows).
6. **Boiler Part Finder stays in Sprint 3** as planned. The "Boiler"
   tile on the homepage links to `/sre/catalog/pillar/boiler-thermal`.
7. **Homepage-only dummy Industry / Application data is seeded** to
   power the four / three tiles on the homepage. These are not the full
   landing pages from §14 / §15; that is Sprint 3. The same records
   are visible to Sprint 3 work later without remapping.

## 4. URL layout

| URL | Action | Render target |
|---|---|---|
| `GET /` | New | `views/sre_home.xml` (8 blocks) |
| `GET /sre/catalog` | Keep | `controllers/catalog.py:catalog()` |
| `GET /sre/catalog/pillar/<slug>` | Keep | `controllers/catalog.py:catalog()` |
| `GET /sre/catalog/family/<slug>` | Keep | `controllers/catalog.py:catalog()` |
| `GET /shop` | New | 301 → `/sre/catalog` (preserve query) |
| `GET /shop/page/<int:page>` | New | 301 → `/sre/catalog?page=<n>` |
| `GET /shop/pillar/<slug>` | New | 301 → `/sre/catalog/pillar/<slug>` |
| `GET /shop/pillar/<slug>/page/<int:page>` | New | 301 → `/sre/catalog/pillar/<slug>?page=<n>` |
| `GET /shop/family/<slug>` | New | 301 → `/sre/catalog/family/<slug>` |
| `GET /shop/family/<slug>/page/<int:page>` | New | 301 → `/sre/catalog/family/<slug>?page=<n>` |
| `GET /shop/search_suggest` | Keep | `controllers/search_suggest.py` |
| `GET /shop/<product>` | Keep | Odoo native product detail (inherits `sre_product_detail_inherit`) |
| `GET /rfq` | Keep | RFQ basket + submit (Sprint 1 already verified) |

Redirects use `request.redirect(target, code=301, local=False)`.

## 5. Components

### 5.1 Catalog controller redirect

In `controllers/shop.py`, replace the body of `SreWebsiteSale.shop()`
with a redirect that maps `pillar_slug` / `family_slug` / `page` /
`?query` to the matching `/sre/catalog[...]` URL. Delete the
`SreWebsiteSale` overrides that extend `WebsiteSale` (search / domain
hooks / additional values) — those only mattered while the
`/shop/pillar/<slug>` page was the actual catalog. The canonical
catalog at `/sre/catalog` does its own product lookup in
`SreCatalog.catalog()`.

The Odoo 19 controller hook names are removed; nothing else in the
codebase calls them.

### 5.2 Homepage controller

`controllers/home.py` exposes a single route:

```
@http.route("/", type="http", auth="public", website=True, sitemap=True)
def home(self, **kw):
    return request.render("mechanic_workshop.sre_home_page", {...})
```

The QWeb context carries:

- `pillars` — `request.website.sre_visible_pillars` (same helper used by
  the catalog and the top nav).
- `industries` — `request.env["sre.industry"].sudo().search([])` ordered
  by name, limited to four (Manufacturing, Food & Beverage, Hotel &
  Resort, Chemical).
- `applications` — `request.env["sre.application"].sudo().search([])`
  ordered by name, limited to three (Boiler Water Level Control, Steam
  System, HVAC Control).
- `featured_products` — top three published demo products ordered by
  `website_sequence asc, name asc`, rendered as `sre-tile` rows.

### 5.3 Homepage template

`views/sre_home.xml` is one QWeb template that renders the full page.
It reuses `mechanic_workshop.sre_home_styles` (the SCSS in
`static/src/scss/sre_home.scss`) and reuses the existing
`sre-pillars-nav` block, the `sre-search` widget, and the `sre-tile`
row markup. The eight blocks in order:

1. **Hero** — h1 "Industrial HVAC, Boiler & Process Equipment"; sub
   line "Components. Spare Parts. Controls. Instrumentation." One
   dense background band, no banner image, no marketing carousel.
2. **Search bar** — `<form action="/sre/catalog" method="get">` with
   a single input named `search`, placeholder "Search by Part
   Number, Model, Brand or Product", submit button.
3. **Quick Access** — 8 pillar tiles in a 4 × 2 grid; each tile
   shows the pillar short label and links to
   `/sre/catalog/pillar/<slug>`. Same hover state as the McMaster
   rows.
4. **Shop by Industry** — 4 industry tiles in a 4 × 1 grid; each
   tile shows the industry name and a product count (products with
   this industry in `industry_ids`); each tile links to
   `/sre/catalog?industry=<slug>` (the catalog controller extends
   the domain if `industry` is in the query).
5. **Shop by Application** — 3 application tiles, same shape as
   industry tiles, links to `/sre/catalog?application=<slug>`.
6. **Featured Categories** — three `sre-tile` rows rendered via the
   same template fragment the catalog uses. Demonstrates the row
   layout in-place; provides concrete click targets.
7. **Technical Resources** — two columns: "Browse Catalog"
   (`/sre/catalog`) and "Submit an RFQ" (`/rfq`). Both render as
   dense text-link rows, not cards.
8. **Request a Quote** — the same blue lead-magnet CTA card from
   the catalog page, promoting the engineering-review offer.

Footer is a minimal block (SRE Commercial © 2026, language switch).
The Odoo default footer is suppressed on `/` by inheriting
`website.layout` and replacing the footer xpath for the home route
only. No other page is affected.

### 5.4 Catalog extension for `?industry=<slug>` / `?application=<slug>`

In `controllers/catalog.py`, extend `SreCatalog.catalog()` to read
`kw.get("industry")` and `kw.get("application")` and add the
corresponding M2M filter to the product domain. Empty result
renders the same "No products match the current filters." message
used by the table view today. No new template; the existing tile
markup handles empty state.

### 5.5 Homepage seed data

`data/sre_home_seed.xml` adds 4 `sre.industry` rows and 3
`sre.application` rows:

| Kind | External ID | Name |
|---|---|---|
| Industry | `sre_industry_home_manufacturing` | Manufacturing |
| Industry | `sre_industry_home_food_beverage` | Food & Beverage |
| Industry | `sre_industry_home_hotel_resort` | Hotel & Resort |
| Industry | `sre_industry_home_chemical` | Chemical |
| Application | `sre_application_home_boiler_water` | Boiler Water Level Control |
| Application | `sre_application_home_steam` | Steam System |
| Application | `sre_application_home_hvac_control` | HVAC Control |

Two of the application rows get M2M `product.template` bindings:

- `sre_application_home_boiler_water` ↔ `sre_demo.product_demo_v_001`
  (Demo Valve 001) — illustrative-only binding per AC-8.
- `sre_application_home_hvac_control` ↔ `sre_demo.product_demo_p_001`
  (Demo Pump 001).

These are demo bindings only. Sprint 3 will populate the full PIM V2
mapping.

### 5.6 SCSS additions

`static/src/scss/sre_home.scss` defines:

- `.sre-home` — page wrapper, white background.
- `.sre-home__hero` — full-bleed band, industrial-blue background,
  white H1, 56 px on desktop, 32 px on mobile.
- `.sre-home__search` — single-row form, 640 px max-width on
  desktop, full-width on mobile; mono input; square button.
- `.sre-home__pillars` — 4-col grid on desktop, 2-col on tablet,
  1-col on mobile.
- `.sre-home__taxonomy` — same grid for industries and applications.
- `.sre-home__featured` — reuses `.sre-catalog` row layout.
- `.sre-home__resources` — 2-col block, dense rows.
- `.sre-home__cta` — same `.sre-lead` card reused.
- Mobile breakpoint at `@media (max-width: 768px)`.

All values use existing SRE design tokens (`--sre-blue`,
`--sre-fg-faint`, etc.) from `sre_tokens.scss`. No new tokens.

### 5.7 Top-nav fix

In `views/website_sale_header.xml`:

- `<a href="/shop">` (logo) becomes `<a href="/">`.
- The 8-pillar `<a t-att-href="'/shop/pillar/%s' % pillar.slug">`
  becomes `<a t-att-href="'/sre/catalog/pillar/%s' % pillar.slug">`.
- The mobile drawer repeats the same change.

Active-pillar detection already uses the URL slug; once the nav links
change, the active state automatically tracks `/sre/catalog/pillar/<slug>`.

## 6. Data flow

1. Guest visits `GET /`.
2. `controllers/home.py:home()` builds context.
3. `views/sre_home.xml` renders with `web.assets_frontend` (which now
   includes `sre_home.scss`).
4. Guest clicks "Valves" tile → `GET /sre/catalog/pillar/valves`.
5. `controllers/catalog.py:catalog()` resolves pillar + products, renders
   `views/sre_catalog.xml`.
6. Guest types `Danfoss` in search → `GET /sre/catalog?search=Danfoss`.
7. Same controller; product domain uses the public search path in
   `controllers/catalog.py`.
8. Guest types `/shop/pillar/boiler-thermal` in the address bar → 301 to
   `/sre/catalog/pillar/boiler-thermal`.

## 7. Error handling

- 301 redirect must always carry `Location`; missing query string is
  fine, empty string is fine. `request.redirect` handles this.
- Redirect target URL is built from validated slugs only; no user input
  is interpolated, so no XSS or open-redirect risk.
- Homepage controller runs as `auth="public"`; only reads
  public-published taxonomies and products. Privacy fields
  (`product.brand.partner_id`, `standard_price`, `supply_status`) are
  never read.
- Empty industries / applications lists render as a single
  empty-state row ("No industries seeded yet." / "No applications
  seeded yet.") so the homepage never crashes if seed data is wiped.
- Featured products list defaults to `product.template` empty browse
  when no `is_published=True sale_ok=True` record exists; the
  Featured block hides itself rather than render an empty header.

## 8. Testing

### 8.1 Automated

`scripts/agent_check.sh` already covers:

- Module installed (`ir.module.module.state == 'installed'`).
- 14 existing assertions continue to pass.

Add one assertion after this feature:

- `homepage_route_returns_200` — `curl -fsS -o /dev/null -w "%{http_code}"
  http://localhost:8080/` returns `200`.

Manual browser checks (Firefox desktop 1280 + Firefox mobile 390):

- `/` renders 8 blocks with no horizontal scroll.
- `/shop/pillar/boiler-thermal` returns 301 and the redirected page
  renders identically to `/sre/catalog/pillar/boiler-thermal`.
- `/sre/catalog/pillar/valves` still renders McMaster rows.
- `/?search=Danfoss` works the same way (form GET).
- `/shop?search=DMV-001` returns 301 → `/sre/catalog?search=DMV-001` →
  Demo Valve 001 is the first row.

## 9. Definition of done

A feature is done only when:

- All ACs below pass with fresh evidence.
- The new files exist in the repo and are committed.
- `./scripts/update-module.sh mechanic_workshop` updates cleanly.
- `./scripts/agent_check.sh` exits 0.
- No new traceback or critical entry appears in
  `docker compose -p odoo_mechanic logs --tail=200 odoo`.
- 3 new screenshots saved to `docs/sre_visual_evidence/before/`:
  `home.png`, `home_mobile.png`, `redirect_pillar_boiler.png`.
- `docs/FEATURE_LIST.json` gains feature `sre-homepage-and-redirect`
  with status `implemented` and AC list below.
- `docs/PROGRESS.md` gains an entry dated 2026-09-08 describing the
  change.

## 10. Acceptance criteria

1. `GET /` returns HTTP 200 to an anonymous request; renders the 8
   blocks in order; H1 reads "Industrial HVAC, Boiler & Process
   Equipment"; search input is present with the expected placeholder.
2. `GET /shop` returns HTTP 301 with `Location: /sre/catalog` (no
   query); `GET /shop?search=DMV-001` returns 301 with
   `Location: /sre/catalog?search=DMV-001` (query preserved).
3. `GET /shop/pillar/boiler-thermal` returns HTTP 301 with
   `Location: /sre/catalog/pillar/boiler-thermal`.
4. `GET /shop/family/<existing-slug>` returns HTTP 301 with
   `Location: /sre/catalog/family/<existing-slug>`.
5. `GET /sre/catalog/pillar/valves` returns 200 with the McMaster row
   layout (no regression).
6. `GET /sre/catalog?search=DMV-001` returns 200 with Demo Valve 001 as
   the first row (SKU exact-match tier 0).
7. `GET /shop/search_suggest?term=Danfoss` returns JSON containing
   empty `products` array when no product matches, with the right
   shape (no regression to the existing endpoint).
8. `GET /rfq` returns 200; the RFQ basket submit path still produces
   one RFQ + one CRM opportunity (no regression).
9. Anonymous (guest) request to any URL above returns 200 or 301; no
   redirect to `/web/login`.
10. Top-nav active state highlights the current pillar on both
    `/sre/catalog/pillar/<slug>` and the post-redirect URL
    `/shop/pillar/<slug>`.
11. `views/website_sale_products.xml` is removed from
    `__manifest__.py`; module update succeeds; no traceback.
12. Three new screenshots saved:
    `docs/sre_visual_evidence/before/home.png`,
    `docs/sre_visual_evidence/before/home_mobile.png`,
    `docs/sre_visual_evidence/before/redirect_pillar_boiler.png`.
13. `./scripts/agent_check.sh` exits 0 with all checks passing.
14. Privacy: `product.brand.partner_id` remains NULL on every brand
    record (existing AC retained); `product.template.standard_price`
    remains 0 on the demo products; no supplier / cost / source field
    is read on `/`.

## 11. Out of scope

- Boiler Part Finder (Sprint 3).
- Cross Reference UI (Sprint 2).
- Compatibility UI (Sprint 2).
- Documents module gating (Sprint 2).
- Industry / Application full landing pages (Sprint 3).
- Dynamic RFQ fields per family (Sprint 2).
- Customer Portal (Sprint 4).
- Customer-specific pricing (Sprint 4).
- Real product images and brand logos (no asset pipeline yet).
- Hero background image / photography.

## 12. Risk

| # | Risk | Mitigation |
|---|---|---|
| 1 | 301 chain confuses browser caching | Redirects are flat (one hop); old `/shop` URLs are not bookmarked by the user today (just typed). |
| 2 | `views/website_sale_products.xml` removal breaks `/shop/<product>` (detail page) | Detail page uses `views/website_sale_product_detail.xml`, not `views/website_sale_products.xml`. Removing the latter does not touch the detail inherit. |
| 3 | Odoo 19 controller inheritance causes the parent `WebsiteSale.shop()` to still match the `/shop` URL | The 301 method takes the same URL list with `type="http", auth="public", website=True`; Odoo routes by first match. The 301 controller is registered first. |
| 4 | Redirect target building concatenates raw query string | `request.httprequest.query_string` is bytes; we decode UTF-8. Only safe characters from the original URL pass through. No user input interpolated into the path. |
| 5 | Industry / Application homepage tiles render empty after seeding | Empty-state fallback rows in the template prevent visual breakage. |
| 6 | Odoo default footer still shows on `/` | Home template replaces the footer xpath; the inherit scope is `/` only. |

## 13. File map

### Add

- `custom_addons/mechanic_workshop/controllers/home.py`
- `custom_addons/mechanic_workshop/views/sre_home.xml`
- `custom_addons/mechanic_workshop/data/sre_home_seed.xml`
- `custom_addons/mechanic_workshop/static/src/scss/sre_home.scss`

### Modify

- `custom_addons/mechanic_workshop/__manifest__.py` — bump version to
  `19.0.1.7.0`; remove `views/website_sale_products.xml` from data;
  add `views/sre_home.xml`, `data/sre_home_seed.xml`, and
  `static/src/scss/sre_home.scss` to assets.
- `custom_addons/mechanic_workshop/controllers/shop.py` — replace the
  body of `SreWebsiteSale.shop()` with a 301 redirect; delete the
  `_add_search_subdomains_hook`, `_shop_lookup_products`,
  `_get_shop_domain`, and `_get_additional_shop_values` overrides
  (no longer reachable).
- `custom_addons/mechanic_workshop/controllers/catalog.py` — accept
  `?industry=<slug>` and `?application=<slug>` query params.
- `custom_addons/mechanic_workshop/views/website_sale_header.xml` —
  change nav links from `/shop/pillar/<slug>` to
  `/sre/catalog/pillar/<slug>` and logo link to `/`.
- `docs/FEATURE_LIST.json` — add feature
  `sre-homepage-and-redirect` (status `implemented`).
- `docs/PROGRESS.md` — append 2026-09-08 entry.
- `scripts/agent_check.sh` — add the homepage 200 check.

### Screenshots

- `docs/sre_visual_evidence/before/home.png`
- `docs/sre_visual_evidence/before/home_mobile.png`
- `docs/sre_visual_evidence/before/redirect_pillar_boiler.png`
