# SRE Commercial — Odoo 19 CE Digital Product Distribution Platform

**Status:** Design — pending user review
**Date:** 2026-09-07
**Author:** Brainstorming session with user
**Odoo version:** 19.0 Community Edition (`odoo:19.0` Docker image)
**Source brief:** `docs/SRE Commercial Website Transformation Brief.docx.md`
**Source governance:** `docs/SRE_COMMERCIAL_WEBSITE_PIM_MASTER_v2.xlsx - README_GOVERNANCE.csv`

## 1. Goal

Transform the existing Odoo staging template into the **SRE
Commercial — Digital Product Distribution Platform**: an RFQ-first B2B
industrial distribution website for HVAC, Boiler, Pumps, Valves, Heat
Exchangers, Instrumentation, Controls & Automation, and Industrial Spare
Parts. Architecture must scale from a few hundred SKUs to 10,000–100,000+
SKUs without rebuild. **The 10,000+ number is a design target; the
100,000+ figure is NOT yet validated — see §13 Risks #4 and §15
Definition of done. No commitment to "supports 100k SKU" until the
benchmark in Risk #4 passes with synthetic data.**

## 2. Architecture decision (CE-only constraint)

Native Odoo 19 CE Docker image (`odoo:19.0`, 684 addons, all LGPL-3)
provides everything required: `website`, `website_sale`,
`website_sale_stock`, `portal`, `account` (basic), `theme_vehicle`,
`l10n_vn`, `crm`, `repair`, `mrp_repair`, etc. No Enterprise license
required. No replacement of native flows — only extensions, overrides,
and project-owned data.

Modules that do NOT exist in CE and require custom work:
- `documents` (DMS) → replaced by `ir.attachment` + `rights_verified` flag
- `account_accountant` (full accounting) → custom contract pricing
- `account_budget` / `account_reports` (advanced reports) → custom SQL /
  `board` + `spreadsheet` dashboards

## 3. Stack

- Docker project `odoo_sre`, db `sre_commercial`, host ports `8080`/`8083`
- Odoo 19 CE + PostgreSQL 15
- i18n: VN (default) + EN
- Currency: VND (base) + USD (manual rate)
- Theme: `theme_vehicle` as foundation, heavy overrides for industrial
  feel (visual review before Sprint 1.4 — risk if automotive styling
  conflicts with brief's "industrial/premium" direction)
- PIM V2 → Odoo: manual CSV import via Odoo UI (`base_import`)
- Visual stack: clean/structured/industrial palette, no retail bright
  colors, mobile responsive, high information density

## 4. Master workflow

```
Guest/User → Search → Browse (Category / Industry / Application / Boiler Finder)
   → Product Page (technical specs, documents gated by rights_verified,
                   compatibility, cross-reference, RFQ CTA)
   → Add to RFQ (multi-product list, dynamic fields by Family)
   → Submit RFQ → CRM Lead (auto-create partner if guest)
   → Sales team qualify → Sale Order (Quotation) → Send
   → Customer accepts → Delivery → Re-order via Portal
```

## 5. PIM V2 → Odoo data mapping

| PIM V2 entity | Odoo model | Notes |
|---|---|---|
| PRODUCT | `product.template` + `product.product` | One variant per unique SKU |
| CATEGORY | `product.public.category` | Website nav primary |
| PRODUCT FAMILY | `sre.product.family` (custom) | Drives attribute profile + filters + dynamic RFQ fields |
| ATTRIBUTE PROFILE | `product.attribute` + `product.template.attribute.line` | Per-family configuration |
| **BRAND** | **`product.brand` (OCA `product_brand` v19.0.1.0.0)** | **Single source. Public info only (name, logo, description). `partner_id` field MUST stay NULL on every record to avoid leaking supplier identity — see §17 governance and §6 privacy.** |
| MANUFACTURER | `res.partner` (industry=manufacturer) | Public name only |
| SRE SKU | `product.product.default_code` | Indexed, primary identifier |
| OEM PN | `sre.oem.pn` (custom, indexed) | Multi-OEM per SKU |
| MANUFACTURER PN | `product.product.barcode` or custom field | Indexed |
| CROSS REFERENCE | `sre.product.crossref` (custom) | Alternative / Replacement / Related / Accessory |
| COMPATIBILITY | `sre.product.compatibility` (custom) | Equipment / Model / Series / Component |
| DOCUMENT | `ir.attachment` + `rights_verified` flag (custom) | Replaces EE `documents` module |
| INDUSTRY | `sre.industry` (custom) | Many-to-many with product |
| APPLICATION | `sre.application` (custom) | Many-to-many with product |
| BOILER METADATA | `sre.boiler.manufacturer/type/model/component` (custom) | Boiler Finder only |
| PUBLIC PRICE FLAG | `product.template.public_price_approved` (bool, custom, default False) | False → hide price, show RFQ CTA only |
| SUPPLY STATUS (internal) | `product.template.supply_status` (selection, custom) | Record rule: internal group only |

## 6. Privacy / governance enforcement

- `ir.model.access.csv` on every custom model — internal fields read-only
  for portal/public
- Record rules: `supply_status`, `standard_price`, supplier/cost fields
  visible only to `base.group_user`
- View inheritance: hide price block when `public_price_approved=False`
- `ir.attachment` controller override: only serve documents where
  `rights_verified=True`
- **`product.brand` (`OCA/product_brand`)**: keep `partner_id` field
  empty on every brand record, OR override the public view to hide it.
  Reason: linking a brand to its supplier partner would expose
  supplier identity on the public website (violates §17 below).

## 7. Custom modules — full list (4 sprints, 13 modules)

| Sprint | Module | Purpose | Complexity |
|---|---|---|---|
| 1 | `sre_commercial_pim` | Brand, Manufacturer, OEM PN master | S |
| 1 | `sre_commercial_catalog` | Product Family, Attribute Profile, public_price_approved | M |
| 1 | `sre_commercial_search` | Multi-field search (SKU / MPN / OEM / Model / Brand / Cross-ref / Keyword) | M |
| 1 | `sre_commercial_website` | Industrial UX overrides (nav, homepage, category/product page shell) | L |
| 1 | `sre_commercial_rfq` | RFQ foundation (multi-product, basic fields, → CRM Lead) | L |
| 2 | `sre_commercial_filters` | Dynamic technical filters per Family | M |
| 2 | `sre_commercial_rfq_dynamic` | Dynamic RFQ fields per Family + attachments | L |
| 2 | `sre_commercial_crossref` | OEM → SKU → Alternative / Replacement / Related / Accessory | M |
| 2 | `sre_commercial_compatibility` | Equipment matrix | L |
| 2 | `sre_commercial_documents` | ir.attachment wrapper + rights_verified gating | M |
| 3 | `sre_commercial_boiler` | Boiler Part Finder (5-step wizard) | L |
| 3 | `sre_commercial_taxonomy` | Industry + Application + landing pages | M |
| 4 | `sre_commercial_portal` | Saved products, RFQ history, contract pricing, re-order, restricted docs | XL |

## 8. Sprint 1 — Foundation (detail)

### Goal
Search works (multi-field), navigation shows 8 pillars + Industries +
Applications + Tech Library + RFQ, product page renders technical
layout, basic RFQ submits to CRM Lead.

### Custom modules (Sprint 1)

#### `sre_commercial_pim`
- **Brand: NOT custom code.** Depends on OCA `product_brand` (already
  installed v19.0.1.0.0). PIM → `product.brand` import via `base_import`;
  admin manages brands via the native menu **Sales → Configuration →
  Product Brands**. Custom code in this module must NOT add any field
  or model that duplicates Brand.
- Extend `res.partner` selection: `industry = manufacturer / customer /
  vendor / ...` (no `brand` value — Brand lives on `product.brand`).
- New model `sre.oem.pn`: `name`, `manufacturer_id` (res.partner,
  domain `industry=manufacturer`), `notes`.
- Depends: base, contacts, product_brand

#### `sre_commercial_catalog`
- Extend `product.template`:
  - `family_id` (M2O → `sre.product.family`)
  - `public_price_approved` (bool, default False)
  - `supply_status` (selection: available / limited / discontinued)
  - `lead_time_text` (char)
- New model `sre.product.family`: `name`, `code`, `attribute_ids` (M2M →
  `product.attribute`), `description`
- Extend `product.attribute`: `family_ids` (M2M reverse)
- Depends: product, product_attribute

#### `sre_commercial_search`
- Override controller `website_sale.products` to add union domain:
  - `default_code` ILIKE + variants
  - `sre.oem.pn.name` ILIKE (cross-table)
  - `product_brand_id.name` ILIKE (via OCA `product_brand`)
  - `res.partner` manufacturer name ILIKE (manufacturer only — not brand)
  - `name` + `description_sale` keyword
- PostgreSQL `pg_trgm` extension + GIN indexes for fuzzy search
- Depends: website_sale, sre_commercial_pim, sre_commercial_catalog,
  product_brand

#### `sre_commercial_website`
- Override `theme_vehicle`:
  - Top nav: HVAC & Building, Boiler & Thermal, Pumps, Valves, Heat
    Exchangers, Instrumentation, Controls & Automation, Industrial Spare
    Parts + Industries, Applications, Technical Library, RFQ
  - Homepage: hero + big search bar (placeholder "Search by Part Number,
    Model, Brand or Product"), Quick Access, Shop by Industry/Application,
    Featured Categories, Technical Resources, RFQ CTA
  - Category page: technical table layout (list view default, grid optional)
  - Product page shell: technical spec table + RFQ CTA; Documents,
    Compatibility, Cross-ref placeholders (filled in Sprint 2)
- SCSS: clean / structured / industrial palette
- Mobile responsive
- Depends: website, website_sale, theme_vehicle

#### `sre_commercial_rfq`
- New model `sre.rfq`:
  - `name` (sequence), `partner_id` (res.partner), `state` (selection:
    draft / submitted / qualified / lost)
  - `industry_id` (M2O → `sre.industry`), `project_name`,
    `project_location`, `project_stage`, `required_delivery_date`
  - `line_ids` (O2M → `sre.rfq.line`)
  - `attachment_ids` (M2M → `ir.attachment`)
  - `is_public_rfq` (bool, analytics)
- New model `sre.rfq.line`:
  - `rfq_id`, `product_id`, `manufacturer_id`, `model`, `quantity`,
    `uom_id`, `notes`
- Action `submit`: create `crm.lead` (type=opportunity), link back via
  `sre.rfq_id` on lead, copy RFQ lines into description
- Guest submit: auto-create `res.partner` from email if not yet existing
- Depends: crm, sale_management, contacts, mail, sre_commercial_catalog

### Native modules installed (Sprint 1)
`base, mail, product, product_attribute, product_matrix, stock,
purchase_stock, crm, contacts, website, website_sale, website_sale_stock,
sale, sale_management, sale_stock, theme_vehicle, portal (prep only),
l10n_vn, utm, digest, barcodes_gs1_nomenclature, account (basic),
account_payment, payment`

### Sprint 1 acceptance criteria
1. Docker stack runs, all modules install without traceback
2. Admin can create Brand (via OCA `product.brand`, native menu) /
   Manufacturer / OEM PN / Product Family / Product Template with
   variants, assign Family + attributes per profile
3. Public:
   - `/` loads with hero search bar visible
   - Top nav shows 8 pillars + Industries / Applications / Technical
     Library / RFQ
   - `/shop?search=Danfoss` returns matching products (multi-field —
     via `product_brand_id.name`)
   - Category page renders technical table layout (no fashion cards)
   - Product page shows: name, brand (via `product_brand_id`),
     MPN, SRE SKU, technical spec table; price block visible iff
     `public_price_approved=True`, else RFQ CTA only; Documents /
     Compatibility / Cross-ref section placeholders
4. RFQ:
   - Guest adds 3+ products to RFQ list (session), submits with contact
     info + industry / project / delivery date
   - System creates `res.partner` from email if new
   - System creates `crm.lead` opportunity linked to RFQ
   - Admin sees lead in CRM pipeline; native "Convert to Quotation"
     action produces `sale.order` from RFQ lines
5. Privacy:
   - `supply_status` not visible on public product page
   - `standard_price` not visible on public product page
   - `product.brand.partner_id` is empty for every brand record
     (verified in `scripts/agent_check.sh`)
6. i18n / currency: VN default, VND + USD available
7. `./scripts/agent_check.sh` exits 0 with Sprint 1 checks added

### Performance target
- Search returns first page (10 products) in < 500 ms at 10k SKU
  (synthetic test data). The 10k target is committed; the
  "100,000+ SKU" claim in §1 Goal and Risk #4 below are NOT
  committed until the same benchmark is re-run at that scale
  with the same synthetic workload.

## 9. Sprint 2 — Technical Commerce (outline)

- `sre_commercial_filters` — override `website_sale.shop` filter
  sidebar; filter set derived from `product.family.attribute_ids`; sticky
  across nav
- `sre_commercial_rfq_dynamic` — extend `sre.rfq.line` with fields
  configurable per Family: Existing Equipment/OEM, Equipment Model,
  Application, Fluid/Media, Operating Pressure, Operating Temperature,
  Flow Rate, Voltage, Incoterm, Urgency, Replacement/New Installation;
  visibility driven by `sre.product.family.required_rfq_fields`
- `sre_commercial_crossref` — `sre.product.crossref` model:
  source_product_id, target_product_id, type (alternative / replacement
  / related / accessory), oem_pn (original OEM PN that triggered the
  relation), notes; search integration; public display on product page
  without source info
- `sre_commercial_compatibility` — `sre.equipment.manufacturer` (extend
  res.partner), `sre.equipment.model` (name + manufacturer_id + series
  M2M), `sre.product.compatibility` (product_id + equipment_type +
  manufacturer + model_id + series_id + component + application);
  record rule: only verified records shown publicly
- `sre_commercial_documents` — `sre.product.document` wrapper around
  `ir.attachment` with: product_id, attachment_id, document_type
  (datasheet / installation_guide / cad / certificate / technical),
  rights_verified (bool), verified_by, verified_date, public (computed);
  controller override serves public documents only

## 10. Sprint 3 — Discovery (outline)

- `sre_commercial_boiler` — Boiler Part Finder 5-step wizard: Boiler
  Manufacturer → Boiler Type → Boiler Model → Component → Part. Models:
  `sre.boiler.manufacturer`, `sre.boiler.type`, `sre.boiler.model`,
  `sre.boiler.component` (full CRUD each). Pre-seeded with Phase 1
  manufacturers per governance CSV (Boiler Parts). Dedicated
  `/boiler-finder` route with progressive disclosure UI.
- `sre_commercial_taxonomy` — `sre.industry` (name, code, description,
  SEO meta), `sre.application` (same shape); M2M on `product.template`
  (`industry_ids`, `application_ids`); landing pages
  `/industries/<slug>` and `/applications/<slug>` with filtered products;
  auto UTM tagging (`utm.source = industry_slug`,
  `utm.campaign = application_slug`)

## 11. Sprint 4 — B2B Platform (outline)

`sre_commercial_portal` — extends `portal` home:
- RFQ / Quotation / Order history (read from native `crm.lead`,
  `sale.order`)
- Re-order (one-click from sale.order history)
- Saved products (new `sre.saved.product`: partner_id, product_id,
  notes, added_date)
- Saved RFQs (new `sre.saved.rfq`: partner_id, name, line_ids_snapshot,
  submitted_date, state)
- Restricted technical documents (customer-specific access via
  `sre.customer.doc.access` ACL)
- Contract pricing (custom `res.partner.contract_price_ids` M2M:
  product + price override)
- Customer-specific pricing (use `product.pricelist` assignment per
  partner; public price visibility = approved_flag AND user has
  assigned pricelist)
- Delivery / order status (native sale.order + stock.picking)

## 12. Out of scope (Phase 2+)

Production TLS / CDN / monitoring / alerting; real payment provider
integration; real shipping / logistics integration; production SMTP;
backup automation; multi-warehouse (more than default WH/Stock);
supplier portal; AI / chatbot; mobile app; BI dashboards beyond basic
Odoo reports.

## 13. Risks & open questions

| # | Item | Impact | Action |
|---|---|---|---|
| 1 | `theme_vehicle` is automotive — may not fit "industrial / premium" | Visual direction | Review before Sprint 1.4 (`sre_commercial_website`); consider `theme_default` fallback |
| 2 | OCA modules not yet researched | Sprint 1 may need additional modules | Before Sprint 1 start, check: `product_multi_category`, `website_sale_category_clarify`, `connector_search`, `web_responsive` |
| 3 | Document storage volume at 10k SKU × multiple docs | Filestore size, backup | Decide storage strategy before Sprint 2 |
| 4 | Search performance at 100k SKU with cross-ref join | UX (NOT yet committed) | Benchmark pg_trgm in Sprint 1 at **10k SKU first**; the 100k figure is a design aspiration only — no claim of support until benchmark passes at that scale |
| 5 | Multi-warehouse for supplier inventory | Brief doesn't say | Default 1 warehouse; revisit if required |
| 6 | VAT / B2B pricing compliance VN | Invoicing | Verify with accounting |
| 7 | SEO at industry / application landing pages | Discoverability | sitemap.xml + Product schema structured data (Sprint 3) |
| 8 | Manufacturer partner dedup | Data quality | Define merge rule (1:1 vs 1:N) before Sprint 1. **Brand no longer in scope here** — Brand uses OCA `product.brand`, separate dedup logic (unique `name`) |
| 9 | PIM V2 actual xlsx master not yet available | Sprint 1 demo data | Data team to provide; Sprint 1 uses synthetic data |
| 10 | Document governance workflow | Rights Verified | Decide: manual admin toggle or approval flow |
| 11 | `l10n_vn` compatibility with Odoo 19 accounting restructure | Invoicing | Verify on first install |
| 12 | Multi-currency manual USD rate | Treasury | Admin maintains rate; no auto-fetch in CE |
| 13 | Backup / restore strategy | Operations | Define before production |
| 14 | Hosting decision | Operations | Cloud (Hetzner / DO / Vultr) vs on-prem |
| 15 | i18n content workflow | Operations | Decide who translates product names / descriptions to EN |
| 16 | Customer portal signup policy | Sprint 4 | Self-signup vs admin invite-only |
| 17 | GDPR / PDPA VN compliance | Sprint 4 | Customer data retention policy |
| 18 | Customer-specific document ACL (Sprint 4) | Sprint 4 | Define model + ACL rule |
| 19 | OCA `product.brand.partner_id` leak path | Public supplier exposure | `agent_check.sh` must fail if any `product.brand.partner_id` is set; CRM/website views must NOT expose the field publicly |
| 20 | PIM V2 brand master not confirmed | Brand import data | Block on receiving BRAND column from PIM V2 master before bulk import; flag in `docs/PROGRESS.md` if any decision is taken without PIM confirmation |

## 14. Decisions confirmed during brainstorm

1. Module rename: `mechanic_workshop` → `sre_commercial` (matches brief)
2. Research scope: full 4 sprints
3. RFQ backend mapping: CRM Lead (type=opportunity) → sales qualify →
   Sale Order (native convert)
4. PIM V2 → Odoo: manual CSV import via Odoo UI
5. Guest users can submit RFQ (auto-create partner from email)
6. Public pricing: boolean `public_price_approved` per product
7. i18n / currency: VN + EN, VND + USD
8. **Brand model = OCA `product.brand` (single source).** No custom
   `res.partner.industry='brand'`. Manufacturer stays on
   `res.partner.industry='manufacturer'` (different concept from
   Brand; OEM PN domain filter still relies on it).
9. **`product.brand.partner_id` MUST stay NULL on every brand
   record.** Public views must not expose it (privacy §6 above,
   §17 below).
10. **The "100,000+ SKU" figure is NOT a current capability claim.**
    See §1 Goal and Risk #4. Only the 10k SKU perf target is
    committed for Sprint 1.

## 15. Definition of done (project-level)

A sprint / feature is done only when:
- All custom modules in scope install / update without traceback
- All Sprint acceptance criteria pass with evidence captured in
  `docs/PROGRESS.md`
- Native modules kept at default flows (no patches)
- `./scripts/agent_check.sh` exits 0 with sprint-specific checks
- Privacy / governance rules enforced and verified
- Risk / open question items that block the sprint are resolved

## 16. Items pending PIM V2 confirmation

The following items depend on data that lives in the PIM V2 master
spreadsheet. Until the data team confirms each row, the Odoo side
must use the placeholder default and the decision must be recorded in
`docs/PROGRESS.md` under a "pending PIM" subsection.

| Item | Odoo placeholder | What PIM V2 must confirm |
|---|---|---|
| Brand list (the master set of brands) | empty `product.brand` table; admin creates manually | The exact BRAND column values (canonical names) and the count. Brand names drive search, filter, sitemap, and OEM PN lookup. |
| Brand logos | `product.brand.logo` left empty | Whether PIM V2 carries logo binary / URL. If yes, pipeline for the asset. |
| Brand localization (VN/EN) | ENG name in `name`, no VN translation | Whether PIM V2 carries a VN display name field. |
| Brand ↔ Manufacturer mapping | not modelled | In many B2B industrial cases Brand = Manufacturer; in others Brand is a distributor label. PIM V2 must clarify before any join is built. |
| Brand dedup rule | unique `name` | Whether case/whitespace insensitive uniqueness is required. |
| Manufacturer ↔ Partner link | OEM PN `manufacturer_id` → `res.partner` | The canonical Manufacturer name list in PIM V2 (drives `sre.oem.pn` domain filter). |
| 100k SKU feasibility | not yet tested | N/A — see §13 Risk #4; the question is not data-driven, it is workload-driven. |

Any code or import that depends on a row above must be marked
`# TODO(pim-v2): <which row>` and recorded in PROGRESS.
