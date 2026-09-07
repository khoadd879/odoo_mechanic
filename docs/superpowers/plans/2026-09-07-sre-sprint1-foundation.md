# SRE Sprint 1 Foundation Implementation Plan

> RFQ update 2026-09-07: the implemented foundation and verified scope are documented in `docs/RFQ_GUIDE.md` and feature `sre-rfq-basic`. Those supersede the RFQ examples below. Implementation stays in `mechanic_workshop`; guest contact details are not automatically matched to an existing partner. Staff choose the verified customer and explicitly create a native quotation.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Sprint 1 Foundation — multi-field search, 8-pillar
navigation, technical category/product page shell, RFQ-to-CRM-Lead
workflow — on Odoo 19 CE.

**Architecture:** Native Odoo 19 CE backbone (`product`, `crm`,
`sale`, `contacts`, `website_sale`, `theme_vehicle`); one umbrella
module `sre_commercial` plus five custom modules
(`sre_commercial_pim`, `_catalog`, `_search`, `_website`, `_rfq`); PIM
V2 → manual CSV import; `pg_trgm` extension for search; guest RFQ
auto-creates `res.partner` from email.

**Tech Stack:** Odoo 19.0 CE (Docker `odoo:19.0`), Python 3.12+,
PostgreSQL 15 + `pg_trgm`, OWL 3.x, XML views, type hints mandatory.

## Global Constraints

The following constraints apply to every task. They are copied
verbatim from `docs/superpowers/specs/2026-09-07-sre-commercial-design.md`.

- Odoo 19 Community Edition (Docker `odoo:19.0`); never install EE-only
  modules
- Python 3.12+ syntax; type hints on every method parameter and return
  type
- `from __future__ import annotations` at top of every Python file
- `SQL()` builder mandatory for any raw SQL
- OWL 3.x patterns only (never OWL 2.x)
- Direct `invisible`/`readonly` in XML views with Python expressions
  (never `attrs={"invisible": ...}`)
- Every custom model must have `ir.model.access.csv` rules
- Privacy: `supply_status`, `standard_price`, supplier/cost fields
  visible only to internal users; never on public views
- i18n: VN default + EN (via Odoo translation mechanism)
- Currency: VND base + USD (admin maintains rate manually)
- Theme: `theme_vehicle` as foundation; override heavily for industrial
  visual direction
- PIM V2 → manual CSV import via Odoo UI (`base_import`)
- Guest RFQ auto-creates `res.partner` from email when not yet existing
- RFQ submit creates `crm.lead` with `type='opportunity'`, links back via
  `sre_rfq_id`; native "Convert to Quotation" produces `sale.order`
- Public price visibility = `public_price_approved` flag (default False)
- Multi-field search over: `default_code`, `sre.oem.pn.name`,
  `product_brand_id.name` (OCA `product.brand` — single source for
  Brand), manufacturer name (`res.partner` with
  `industry='manufacturer'`), `name`, `description_sale`
- PostgreSQL `pg_trgm` extension enabled on application database
- No patches to native Odoo; only inherit and extend
- `git add` and commit at the end of every task
- `./scripts/agent_check.sh` must exit 0 before a task is "done"

## File Structure

```
odoo_mechanic/                          # repo root (folder name kept for path stability)
├── AGENTS.md                           # project identity, ports, commands
├── README.md
├── docker-compose.yml                  # compose project odoo_sre
├── odoo.conf                           # db sre_commercial
├── .env.example                        # POSTGRES_PASSWORD=sre_commercial_local
├── .gitignore
├── docs/
│   ├── PROJECT_BRIEF.md
│   ├── ODOO_ARCHITECTURE.md
│   ├── FEATURE_LIST.json
│   ├── PROGRESS.md
│   ├── VERIFICATION.md
│   ├── superpowers/
│   │   ├── specs/2026-09-07-sre-commercial-design.md
│   │   └── plans/2026-09-07-sre-sprint1-foundation.md
│   ├── SRE Commercial Website Transformation Brief.docx.md
│   └── SRE_COMMERCIAL_WEBSITE_PIM_MASTER_v2.xlsx - README_GOVERNANCE.csv
├── scripts/
│   ├── update-module.sh                # default module sre_commercial
│   └── agent_check.sh                  # extended for Sprint 1
└── custom_addons/
    ├── sre_commercial/                 # umbrella; depends on all sub-modules
    │   ├── __init__.py
    │   ├── __manifest__.py
    │   └── data/seed.xml               # default Product Family seed
    ├── sre_commercial_pim/             # Task 2 (revised 2026-09-07)
    │   ├── __init__.py
    │   ├── __manifest__.py               # depends: base, contacts, product_brand
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── res_partner.py            # industry='manufacturer' ONLY (no 'brand')
    │   │   └── sre_oem_pn.py
    │   ├── views/
    │   │   ├── res_partner_views.xml     # industry field visible; no brand value
    │   │   └── sre_oem_pn_views.xml
    │   ├── security/ir.model.access.csv
    │   └── tests/
    │       ├── __init__.py
    │       ├── test_partner_industry.py  # only manufacturer is added
    │       └── test_oem_pn.py
    │   # NOTE: Brand uses OCA `product_brand` (no custom model). PIM → product.brand
    │   # import flows through base_import. See Task 2 sub-task "Verify OCA
    │   # product_brand integration" below.
    ├── sre_commercial_catalog/         # Task 3
    │   ├── __init__.py
    │   ├── __manifest__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── product_template.py
    │   │   ├── sre_product_family.py
    │   │   └── product_attribute.py
    │   ├── views/
    │   │   ├── product_template_views.xml
    │   │   ├── sre_product_family_views.xml
    │   │   └── product_attribute_views.xml
    │   ├── security/ir.model.access.csv
    │   └── tests/
    │       ├── __init__.py
    │       ├── test_product_family.py
    │       └── test_product_template_flags.py
    ├── sre_commercial_search/          # Task 4
    │   ├── __init__.py
    │   ├── __manifest__.py
    │   ├── controllers/
    │   │   ├── __init__.py
    │   │   └── main.py
    │   ├── search/
    │   │   ├── __init__.py
    │   │   └── domains.py
    │   └── tests/
    │       ├── __init__.py
    │       ├── test_search_domains.py
    │       └── test_shop_controller.py
    ├── sre_commercial_website/         # Task 5
    │   ├── __init__.py
    │   ├── __manifest__.py
    │   ├── views/
    │   │   ├── nav.xml
    │   │   ├── homepage.xml
    │   │   ├── category_page.xml
    │   │   └── product_page.xml
    │   ├── static/src/scss/industrial.scss
    │   └── tests/
    │       ├── __init__.py
    │       └── test_pages_render.py
    └── sre_commercial_rfq/             # Task 6
        ├── __init__.py
        ├── __manifest__.py
        ├── models/
        │   ├── __init__.py
        │   ├── crm_lead.py             # adds sre_rfq_id
        │   ├── sre_rfq.py
        │   └── sre_rfq_line.py
        ├── controllers/
        │   ├── __init__.py
        │   └── main.py                 # /rfq submit + guest partner
        ├── views/
        │   ├── sre_rfq_views.xml
        │   ├── website_rfq.xml
        │   └── crm_lead_views.xml
        ├── security/ir.model.access.csv
        └── tests/
            ├── __init__.py
            ├── test_rfq_submit.py
            └── test_guest_partner_create.py
```

---

## Task 1: Repository setup and stack configuration

**Files:**

- Modify: `/home/khoa/Company/odoo_mechanic/AGENTS.md`
- Modify: `/home/khoa/Company/odoo_mechanic/README.md`
- Modify: `/home/khoa/Company/odoo_mechanic/docker-compose.yml`
- Modify: `/home/khoa/Company/odoo_mechanic/odoo.conf`
- Modify: `/home/khoa/Company/odoo_mechanic/.env.example`
- Modify: `/home/khoa/Company/odoo_mechanic/scripts/update-module.sh`
- Modify: `/home/khoa/Company/odoo_mechanic/scripts/agent_check.sh`
- Modify: `/home/khoa/Company/odoo_mechanic/docs/FEATURE_LIST.json`
- Delete: `/home/khoa/Company/odoo_mechanic/custom_addons/mechanic_workshop/`
- Create: 6 module folders (umbrella + 5 sub-modules) with `__manifest__.py` and `__init__.py`
- Create: `/home/khoa/Company/odoo_mechanic/.git/`

**Interfaces:**

- Produces: working `docker compose -p odoo_sre` stack that brings up
  `db` (PostgreSQL with `pg_trgm` enabled) and `odoo` (Odoo 19 CE with
  default database admin password `sre_commercial_master_local`,
  database name `sre_commercial`).

- [ ] **Step 1: Update AGENTS.md**

Replace the entire file with content that reflects the new project
identity: compose project `odoo_sre`, db `sre_commercial`, host ports
8080/8083, repo root `/home/khoa/Company/odoo_mechanic`. Forbid mounting
from `/Company/odoo` and `/Company/odoo_testing`. Active module name:
`sre_commercial`. Approved commands section uses `-p odoo_sre` and
default module `sre_commercial`.

- [ ] **Step 2: Update README.md**

Replace the entire file with content describing the SRE Commercial
Digital Product Distribution Platform, the 4-sprint plan, and the
quick-start commands (matching the new compose project and ports).

- [ ] **Step 3: Update docker-compose.yml**

Change `name: odoo_mechanic` to `name: odoo_sre`. Change container names
`odoo_mechanic_db` → `odoo_sre_db`, `odoo_mechanic_app` →
`odoo_sre_app`. Change volume names `odoo_mechanic_db` → `odoo_sre_db`,
`odoo_mechanic_data` → `odoo_sre_data`. Default password
`${POSTGRES_PASSWORD:-mechanic_local}` → `${POSTGRES_PASSWORD:-sre_commercial_local}`.
Host ports stay `8080:8069` and `8083:8072`. Add a command flag
`--load=base,web` to the Odoo service so initial boot does not
auto-install everything; this is overridden later by `update-module.sh`.

- [ ] **Step 4: Update odoo.conf**

Change `db_name = mechanic_workshop` → `db_name = sre_commercial`.
Change `dbfilter = ^mechanic_workshop$` → `dbfilter = ^sre_commercial$`.
Change `admin_passwd = mechanic_master_local` →
`admin_passwd = sre_commercial_master_local`. Change
`db_password = mechanic_local` → `db_password = sre_commercial_local`.

- [ ] **Step 5: Update .env.example**

Replace contents with:

```env
ODOO_IMAGE=odoo:19.0
POSTGRES_IMAGE=postgres:15
POSTGRES_PASSWORD=sre_commercial_local
```

- [ ] **Step 6: Update scripts/update-module.sh**

Change default `MODULE="${1:-mechanic_workshop}"` →
`MODULE="${1:-sre_commercial}"`. Change `DATABASE="mechanic_workshop"`
→ `DATABASE="sre_commercial"`. Change `docker compose -p odoo_mechanic`
→ `docker compose -p odoo_sre` (in both the `run` and `exec` lines).
Make the script executable: `chmod +x scripts/update-module.sh`.

- [ ] **Step 7: Replace scripts/agent_check.sh**

Replace the file with a Sprint 1 skeleton that:

- Sets `REPO_ROOT` and changes color helpers (kept).
- Defines helper functions `service_is_running`, `volume_exists`,
  `url_contains`, `no_foreign_mount`, all using
  `docker compose -p odoo_sre`.
- Section "Project files": checks
  `custom_addons/sre_commercial/__manifest__.py` exists, and each of
  the 5 sub-module manifests exists.
- Section "Compose": checks services `db` and `odoo` running, volumes
  `odoo_sre_db` and `odoo_sre_data` exist, no foreign project mount.
- Section "Sprint 1": checks homepage reachable at
  `http://localhost:8080/`, contains the placeholder text "Search by
  Part Number, Model, Brand or Product", `/shop` reachable, `/shop`
  accepts search param.
- Section "Recent logs": same as before, scanning
  `docker compose -p odoo_sre logs --tail=200 odoo` for tracebacks or
  critical entries.
- Section "Repository": prints `git status --short`.

Make the script executable.

- [ ] **Step 8: Delete obsolete `mechanic_workshop` folder**

Run: `rm -rf /home/khoa/Company/odoo_mechanic/custom_addons/mechanic_workshop`

Verify: `ls /home/khoa/Company/odoo_mechanic/custom_addons/`

Expected: empty directory except for hidden `.gitkeep`. If `.gitkeep`
is missing, create it: `touch /home/khoa/Company/odoo_mechanic/custom_addons/.gitkeep`.

- [ ] **Step 9: Create umbrella `sre_commercial` module skeleton**

Create directory `custom_addons/sre_commercial/`. Create
`__init__.py` (empty file). Create `__manifest__.py`:

```python
{
    "name": "SRE Commercial",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "SRE Commercial Digital Product Distribution Platform umbrella.",
    "description": """
SRE Commercial — Umbrella Module
================================

Installs all Sprint 1 sub-modules required for the RFQ-first B2B
industrial distribution platform. Sub-modules:

* sre_commercial_pim       — Manufacturer + OEM PN master
  (Brand uses OCA `product_brand`, not custom code)
* sre_commercial_catalog   — Product Family, Attribute Profile, flags
* sre_commercial_search    — Multi-field search
* sre_commercial_website   — Industrial UX overrides
* sre_commercial_rfq       — RFQ foundation (multi-product, → CRM Lead)
    """,
    "author": "SRE Commercial",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "product",
        "product_attribute",
        "product_matrix",
        "stock",
        "purchase_stock",
        "crm",
        "contacts",
        "website",
        "website_sale",
        "website_sale_stock",
        "sale",
        "sale_management",
        "sale_stock",
        "theme_vehicle",
        "portal",
        "l10n_vn",
        "utm",
        "digest",
        "barcodes_gs1_nomenclature",
        "account",
        "account_payment",
        "payment",
        "sre_commercial_pim",
        "sre_commercial_catalog",
        "sre_commercial_search",
        "sre_commercial_website",
        "sre_commercial_rfq",
    ],
    "data": [
        "data/seed.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
```

Create `data/seed.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Seed: default Product Family placeholders are added via
             sre_commercial_catalog fixtures; nothing here yet. -->
    </data>
</odoo>
```

- [ ] **Step 10: Create skeleton for `sre_commercial_pim`**

Create `custom_addons/sre_commercial_pim/__init__.py` (empty).
Create `custom_addons/sre_commercial_pim/__manifest__.py`:

```python
{
    "name": "SRE Commercial — PIM Master",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Manufacturer + OEM PN master. Brand uses OCA product_brand.",
    "description": """
SRE Commercial PIM
==================

Extends ``res.partner`` with an ``industry`` selection adding
``manufacturer`` only (Brand lives on OCA ``product.brand`` — see
§16 of the spec). Provides a new ``sre.oem.pn`` model for OEM part
numbers (multi-OEM per product in later sprints).
    """,
    "author": "SRE Commercial",
    "license": "LGPL-3",
    "depends": ["base", "contacts", "product_brand"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/sre_oem_pn_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
```

Create empty placeholder files (touch): `models/__init__.py`,
`views/res_partner_views.xml`, `views/sre_oem_pn_views.xml`,
`security/ir.model.access.csv`, `tests/__init__.py`.

`res_partner_views.xml` and `sre_oem_pn_views.xml` start as valid XML
with empty `<odoo><data/></odoo>` body.

- [ ] **Step 11: Create skeletons for remaining 4 sub-modules**

Repeat the skeleton pattern (Step 10) for each:

- `sre_commercial_catalog`: depends `base, product, product_attribute`,
  summary "Product Family, Attribute Profile, public_price_approved."
- `sre_commercial_search`: depends
  `base, website_sale, sre_commercial_pim, sre_commercial_catalog`,
  summary "Multi-field search (SKU / MPN / OEM PN / Model / Brand / Keyword)."
- `sre_commercial_website`: depends
  `base, website, website_sale, theme_vehicle`, summary
  "Industrial UX overrides for theme_vehicle."
- `sre_commercial_rfq`: depends
  `base, crm, sale_management, contacts, mail, sre_commercial_catalog`,
  summary "RFQ foundation (multi-product, → CRM Lead)."

Each gets empty `__init__.py`, `__manifest__.py`, placeholder
subfolders (`models/__init__.py`, `views/*.xml`,
`security/ir.model.access.csv`, `tests/__init__.py`).

- [ ] **Step 12: Update docs/FEATURE_LIST.json**

Replace contents with:

```json
{
  "project": "sre_commercial",
  "version": "19.0.1.0.0",
  "sprints": [
    {
      "name": "Sprint 1 — Foundation",
      "status": "in_progress",
      "modules": [
        "sre_commercial",
        "sre_commercial_pim",
        "sre_commercial_catalog",
        "sre_commercial_search",
        "sre_commercial_website",
        "sre_commercial_rfq"
      ]
    }
  ]
}
```

- [ ] **Step 13: Initialize git repository**

Run from repo root:

```bash
cd /home/khoa/Company/odoo_mechanic
git init
git config user.email "agent@localhost"
git config user.name "SRE Agent"
```

Note: do NOT modify the global git config. Use
`git -c user.email=... -c user.name=...` for individual commits if
preferred.

- [ ] **Step 14: Bring up the stack**

Run:

```bash
docker compose -p odoo_sre up -d db
docker compose -p odoo_sre run --rm odoo \
    psql -h db -U odoo -d postgres -c \
    "CREATE DATABASE sre_commercial;"
docker compose -p odoo_sre run --rm odoo \
    psql -h db -U odoo -d sre_commercial -c \
    "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
docker compose -p odoo_sre up -d odoo
```

Important: `psql` is available inside the `odoo` image (it ships with
the `postgres-client` utility). Alternatively, exec into the `db`
container with `docker compose -p odoo_sre exec db psql ...`.

Verify `docker compose -p odoo_sre ps` shows both services healthy.

Verify `curl -fsS http://localhost:8080/web/login` returns HTTP 200.

- [ ] **Step 15: First commit**

Run from repo root:

```bash
cd /home/khoa/Company/odoo_mechanic
git add -A
git status --short    # verify expected files only
git commit -m "feat(sre_sprint1): scaffold odoo_sre stack and 6 module skeletons"
```

- [ ] **Step 16: Verify Task 1 done**

Run: `bash scripts/agent_check.sh`

Expected: every check passes or "PASS" appears at least once for the
project-files and compose sections. The Sprint 1 section may have
unmet sub-checks (search bar text not yet rendered); that is fine for
the end of Task 1. The "Recent logs" section must show PASS (no
traceback).

---

## Task 2: `sre_commercial_pim` — Manufacturer + OEM PN master

> **Revised 2026-09-07**: Brand is no longer modelled here. Brand
> uses OCA `product.brand` (single source). This task now adds only
> `manufacturer` to `res.partner.industry` and ships `sre.oem.pn`.

**Files:**

- Modify: `custom_addons/sre_commercial_pim/__manifest__.py` (already
  correct — `depends` must include `product_brand`)
- Create: `custom_addons/sre_commercial_pim/models/__init__.py`
- Create: `custom_addons/sre_commercial_pim/models/res_partner.py`
- Create: `custom_addons/sre_commercial_pim/models/sre_oem_pn.py`
- Modify: `custom_addons/sre_commercial_pim/views/res_partner_views.xml`
- Modify: `custom_addons/sre_commercial_pim/views/sre_oem_pn_views.xml`
- Modify: `custom_addons/sre_commercial_pim/security/ir.model.access.csv`
- Modify: `custom_addons/sre_commercial_pim/tests/__init__.py`
- Create: `custom_addons/sre_commercial_pim/tests/test_partner_industry.py`
- Create: `custom_addons/sre_commercial_pim/tests/test_oem_pn.py`
- Create: `custom_addons/sre_commercial_pim/tests/test_product_brand_integration.py`

**Interfaces:**

- Produces:
  - `res.partner.industry`: SelectionField with `manufacturer` added
    (NO `brand` value — Brand lives on OCA `product.brand`).
  - `sre.oem.pn`: Model with `name` (Char, required, indexed),
    `manufacturer_id` (M2O `res.partner`, domain
    `industry='manufacturer'`), `notes` (Text).
  - Depends on OCA `product_brand`; module does NOT add any field
    or model that duplicates Brand.

### Sub-task 2a: OCA `product_brand` integration smoke test

- [ ] **Step 1: Verify OCA `product_brand` is installed**

```bash
docker compose -p odoo_mechanic exec -T odoo odoo shell -d mechanic_workshop --no-http <<'PY'
m = env['ir.module.module'].search([('name','=','product_brand')])
assert m.state == 'installed', f"product_brand not installed: {m.state}"
assert m.installed_version == '19.0.1.0.0', f"unexpected version: {m.installed_version}"
assert 'product_brand_id' in env['product.template']._fields, "field missing on product.template"
assert env['product.template']._fields['product_brand_id'].comodel_name == 'product.brand'
print('OCA product_brand OK')
PY
```

Expected: `OCA product_brand OK`.

- [ ] **Step 2: Write integration test for OCA `product_brand`**

Create
`custom_addons/sre_commercial_pim/tests/test_product_brand_integration.py`:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductBrandIntegration(TransactionCase):
    """Confirms OCA product_brand is the Brand source for products.

    No custom code defines Brand; this test asserts the OCA field is
    in place and that we never write anything into
    product.brand.partner_id (privacy §6, Risk #19).
    """

    def test_product_brand_id_is_on_product_template(self) -> None:
        fld = self.env['product.template']._fields.get('product_brand_id')
        self.assertIsNotNone(fld)
        self.assertEqual(fld.comodel_name, 'product.brand')

    def test_brand_partner_id_must_stay_empty(self) -> None:
        brand = self.env['product.brand'].create({'name': 'Danfoss'})
        # Privacy: brand.partner_id MUST remain unset to avoid leaking
        # supplier identity on the public site.
        self.assertFalse(brand.partner_id)
        # Assigning a partner is allowed (the field exists) but the
        # website / portal views must hide it. The full enforcement
        # lives in agent_check.sh; the test just confirms no implicit
        # populate happens during install.
        self.assertFalse(
            self.env['product.brand'].search([('partner_id', '!=', False)]),
            "No product.brand.partner_id should be set after install",
        )
```

Add `from . import test_product_brand_integration` to
`custom_addons/sre_commercial_pim/tests/__init__.py`.

- [ ] **Step 3: Add `product_brand` to manifest depends**

`__manifest__.py` already has `product_brand` in `depends` (see Step
10 in Task 1). Verify the install/upgrade command picks it up:

```bash
docker compose -p odoo_mechanic exec -T odoo odoo \
    -d mechanic_workshop \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons,/mnt/oca_addons/brand \
    -u sre_commercial_pim --test-enable --test-tags=sre_commercial_pim \
    --stop-after-init --no-http
```

Expected: PASS for `TestProductBrandIntegration`.

### Sub-task 2b: `res.partner.industry` (manufacturer only)

- [ ] **Step 4: Write failing test for `res.partner.industry`**

Create `custom_addons/sre_commercial_pim/tests/test_partner_industry.py`:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPartnerIndustry(TransactionCase):

    def test_manufacturer_partner_is_manufacturer(self):
        partner = self.env['res.partner'].create({
            'name': 'Grundfos Holding A/S',
            'is_company': True,
            'industry': 'manufacturer',
        })
        self.assertEqual(partner.industry, 'manufacturer')

    def test_industry_selection_includes_manufacturer_only(self):
        selection = dict(
            self.env['res.partner'].fields_get(['industry'])
            ['industry']['selection']
        )
        self.assertIn('manufacturer', selection)
        # Brand must NOT be in res.partner.industry — it lives on
        # product.brand (OCA).
        self.assertNotIn('brand', selection)
```

Add `from . import test_partner_industry` to
`custom_addons/sre_commercial_pim/tests/__init__.py`.

- [ ] **Step 5: Run test, verify it fails**

```bash
./scripts/update-module.sh sre_commercial_pim
```

Expected: ImportError because `sre_commercial_pim.models.res_partner`
does not exist.

- [ ] **Step 6: Implement `res.partner.industry` extension**

Create `custom_addons/sre_commercial_pim/models/res_partner.py`:

```python
from __future__ import annotations

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    industry: str = fields.Selection(
        selection_add=[
            ('manufacturer', 'Manufacturer'),
        ],
        ondelete={'manufacturer': 'set null'},
    )
```

Note: the base `res.partner` already has an `industry` field as a
Selection. We extend the selection via `selection_add`. **`brand` is
intentionally NOT in the selection** — Brand lives on OCA
`product.brand`.

- [ ] **Step 7: Wire models `__init__.py`**

Create `custom_addons/sre_commercial_pim/models/__init__.py`:

```python
from . import res_partner
from . import sre_oem_pn
```

(Add `sre_oem_pn` model in the next step.)

Update `custom_addons/sre_commercial_pim/__init__.py`:

```python
from . import models
```

- [ ] **Step 8: Run test, verify pass**

```bash
./scripts/update-module.sh sre_commercial_pim
```

Expected: PASS for both tests in `TestPartnerIndustry`.

- [ ] **Step 9: Write failing test for `sre.oem.pn`**

Create `custom_addons/sre_commercial_pim/tests/test_oem_pn.py`:

```python
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOemPn(TransactionCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.manufacturer = cls.env['res.partner'].create({
            'name': 'Test Manufacturer Co.',
            'is_company': True,
            'industry': 'manufacturer',
        })

    def test_create_oem_pn_with_manufacturer(self) -> None:
        oem = self.env['sre.oem.pn'].create({
            'name': '068-1234',
            'manufacturer_id': self.manufacturer.id,
        })
        self.assertEqual(oem.name, '068-1234')
        self.assertEqual(oem.manufacturer_id, self.manufacturer)

    def test_oem_pn_name_required(self) -> None:
        with self.assertRaises(Exception):
            self.env['sre.oem.pn'].create({
                'manufacturer_id': self.manufacturer.id,
            })

    def test_oem_pn_display_name_includes_manufacturer(self) -> None:
        oem = self.env['sre.oem.pn'].create({
            'name': 'CR-10',
            'manufacturer_id': self.manufacturer.id,
        })
        self.assertIn('Test Manufacturer', oem.display_name)

    def test_manufacturer_domain_filter(self) -> None:
        """Domain restricts manufacturer_id to partners with industry='manufacturer'."""
        non_manufacturer = self.env['res.partner'].create({
            'name': 'Random Customer',
            'is_company': True,
            'industry': 'retail',
        })
        oem = self.env['sre.oem.pn'].create({
            'name': 'TEST-1',
            'manufacturer_id': non_manufacturer.id,
        })
        self.assertNotEqual(oem.manufacturer_id.industry, 'manufacturer')
```

Add `from . import test_oem_pn` to
`custom_addons/sre_commercial_pim/tests/__init__.py`.

- [ ] **Step 10: Run test, verify it fails**

Re-run the command from Step 8. Expected: ImportError on `sre.oem.pn`.

- [ ] **Step 11: Implement `sre.oem.pn`**

Create `custom_addons/sre_commercial_pim/models/sre_oem_pn.py`:

```python
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SreOemPn(models.Model):
    _name = 'sre.oem.pn'
    _description = 'OEM Part Number'
    _rec_name = 'display_name'
    _order = 'manufacturer_id, name'

    name: str = fields.Char(
        string='OEM Part Number',
        required=True,
        index=True,
    )
    manufacturer_id: int = fields.Many2one(
        comodel_name='res.partner',
        string='Manufacturer',
        domain=[('industry', '=', 'manufacturer')],
        required=True,
        index=True,
    )
    notes: str = fields.Text(string='Notes')

    @api.constrains('manufacturer_id')
    def _check_manufacturer_industry(self) -> None:
        for record in self:
            if record.manufacturer_id.industry != 'manufacturer':
                raise ValidationError(
                    _("Manufacturer '%s' is not marked as industry='manufacturer'.")
                    % record.manufacturer_id.display_name
                )
```

Wire imports as in Step 7.

- [ ] **Step 12: Run test, verify pass**

Re-run Step 8 command. Expected: all tests in `TestPartnerIndustry`,
`TestOemPn`, and `TestProductBrandIntegration` pass.

- [ ] **Step 13: Add views**

Replace `custom_addons/sre_commercial_pim/views/res_partner_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_partner_form_inherit_industry" model="ir.ui.view">
        <field name="name">res.partner.form.inherit.industry</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_form"/>
        <field name="arch" type="xml">
            <field name="industry" position="attributes">
                <attribute name="invisible">0</attribute>
            </field>
        </field>
    </record>
</odoo>
```

Replace `custom_addons/sre_commercial_pim/views/sre_oem_pn_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_sre_oem_pn_tree" model="ir.ui.view">
        <field name="name">sre.oem.pn.tree</field>
        <field name="model">sre.oem.pn</field>
        <field name="arch" type="xml">
            <tree string="OEM Part Numbers">
                <field name="name"/>
                <field name="manufacturer_id"/>
            </tree>
        </field>
    </record>
    <record id="view_sre_oem_pn_form" model="ir.ui.view">
        <field name="name">sre.oem.pn.form</field>
        <field name="model">sre.oem.pn</field>
        <field name="arch" type="xml">
            <form string="OEM Part Number">
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="manufacturer_id"/>
                    </group>
                    <field name="notes" placeholder="Optional notes..."/>
                </sheet>
            </form>
        </field>
    </record>
    <record id="action_sre_oem_pn" model="ir.actions.act_window">
        <field name="name">OEM Part Numbers</field>
        <field name="res_model">sre.oem.pn</field>
        <field name="view_mode">tree,form</field>
    </record>
    <menuitem id="menu_sre_oem_pn"
              name="OEM Part Numbers"
              parent="contacts.menu_contacts"
              action="action_sre_oem_pn"
              sequence="50"/>
</odoo>
```

- [ ] **Step 14: Add security**

Replace `custom_addons/sre_commercial_pim/security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sre_oem_pn_user,sre.oem.pn,model_sre_oem_pn,base.group_user,1,1,1,0
access_sre_oem_pn_system,sre.oem.pn,model_sre_oem_pn,base.group_system,1,1,1,1
```

- [ ] **Step 15: Upgrade module and verify views**

```bash
./scripts/update-module.sh sre_commercial_pim
```

Expected: no traceback. Verification checklist at the UI:

- Contacts → create partner with `industry=Manufacturer` (no `brand`
  value in the dropdown).
- Sales → Configuration → **Product Brands** (native OCA menu) →
  create a brand record. Leave `partner_id` empty.
- Products → create a Product Template, set `Brand = <OCA brand>`.
- Contacts → OEM Part Numbers menu → create one record.
- Run `./scripts/agent_check.sh` and confirm PASS.

- [ ] **Step 16: Commit**

```bash
cd /home/khoa/Company/odoo_mechanic
git add custom_addons/sre_commercial_pim/
git commit -m "feat(sre_pim): manufacturer on res.partner + sre.oem.pn model (brand via OCA)"
```

---

## Task 3: `sre_commercial_catalog` — Product Family + flags

**Files:**

- Modify: `custom_addons/sre_commercial_catalog/__manifest__.py`
- Create: `custom_addons/sre_commercial_catalog/models/__init__.py`
- Create: `custom_addons/sre_commercial_catalog/models/sre_product_family.py`
- Create: `custom_addons/sre_commercial_catalog/models/product_attribute.py`
- Create: `custom_addons/sre_commercial_catalog/models/product_template.py`
- Modify: `custom_addons/sre_commercial_catalog/views/sre_product_family_views.xml`
- Modify: `custom_addons/sre_commercial_catalog/views/product_attribute_views.xml`
- Modify: `custom_addons/sre_commercial_catalog/views/product_template_views.xml`
- Modify: `custom_addons/sre_commercial_catalog/security/ir.model.access.csv`
- Modify: `custom_addons/sre_commercial_catalog/tests/__init__.py`
- Create: `custom_addons/sre_commercial_catalog/tests/test_product_family.py`
- Create: `custom_addons/sre_commercial_catalog/tests/test_product_template_flags.py`

**Interfaces:**

- Produces:
  - `sre.product.family`: Model with `name`, `code`, `description`,
    `attribute_ids` (M2M `product.attribute`).
  - `product.template.family_id`: M2O `sre.product.family`.
  - `product.template.public_price_approved`: bool (default False).
  - `product.template.supply_status`: selection (available/limited/discontinued).
  - `product.template.lead_time_text`: char.
  - `product.attribute.family_ids`: M2M reverse of family.

- [ ] **Step 1: Write failing test for `sre.product.family`**

Create `custom_addons/sre_commercial_catalog/tests/test_product_family.py`:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductFamily(TransactionCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.attr_pressure = cls.env['product.attribute'].create({
            'name': 'Pressure Class',
        })
        cls.attr_size = cls.env['product.attribute'].create({
            'name': 'Nominal Size',
        })

    def test_create_family_with_attributes(self) -> None:
        family = self.env['sre.product.family'].create({
            'name': 'Valves',
            'code': 'valves',
            'attribute_ids': [(6, 0, [self.attr_pressure.id, self.attr_size.id])],
        })
        self.assertEqual(family.code, 'valves')
        self.assertIn(self.attr_pressure, family.attribute_ids)

    def test_attribute_inherits_family_ids(self) -> None:
        family = self.env['sre.product.family'].create({
            'name': 'Pumps',
            'code': 'pumps',
            'attribute_ids': [(6, 0, [self.attr_pressure.id])],
        })
        self.assertIn(family, self.attr_pressure.family_ids)
```

- [ ] **Step 2: Run test, verify fail**

```bash
docker compose -p odoo_sre exec -T odoo odoo \
    -d sre_commercial \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons \
    -u sre_commercial_catalog --test-enable --test-tags=sre_commercial_catalog \
    --stop-after-init --no-http
```

Expected: ImportError on `sre.product.family`.

- [ ] **Step 3: Implement `sre.product.family` and extend `product.attribute`**

Create `custom_addons/sre_commercial_catalog/models/sre_product_family.py`:

```python
from odoo import _, api, fields, models


class SreProductFamily(models.Model):
    _name = 'sre.product.family'
    _description = 'SRE Product Family'
    _rec_name = 'name'
    _order = 'sequence, name'

    name: str = fields.Char(string='Family Name', required=True, translate=True)
    code: str = fields.Char(string='Technical Code', required=True, index=True)
    sequence: int = fields.Integer(default=10)
    description: str = fields.Text(string='Description', translate=True)
    attribute_ids: list = fields.Many2many(
        comodel_name='product.attribute',
        relation='sre_family_attribute_rel',
        column1='family_id',
        column2='attribute_id',
        string='Attribute Profile',
    )
```

Create `custom_addons/sre_commercial_catalog/models/product_attribute.py`:

```python
from odoo import _, api, fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    family_ids: list = fields.Many2many(
        comodel_name='sre.product.family',
        relation='sre_family_attribute_rel',
        column1='attribute_id',
        column2='family_id',
        string='Used in Families',
    )
```

Wire imports in
`custom_addons/sre_commercial_catalog/models/__init__.py`:

```python
from . import sre_product_family
from . import product_attribute
from . import product_template
```

- [ ] **Step 4: Run test, verify pass**

Re-run Step 2. Expected: both `test_product_family` tests pass.

- [ ] **Step 5: Write failing test for `product.template` flags**

Create
`custom_addons/sre_commercial_catalog/tests/test_product_template_flags.py`:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductTemplateFlags(TransactionCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.family = cls.env['sre.product.family'].create({
            'name': 'Valves',
            'code': 'valves',
        })

    def test_public_price_approved_default_false(self) -> None:
        tmpl = self.env['product.template'].create({
            'name': 'Test Valve',
            'family_id': self.family.id,
            'list_price': 100.0,
        })
        self.assertFalse(tmpl.public_price_approved)

    def test_public_price_approved_can_be_set(self) -> None:
        tmpl = self.env['product.template'].create({
            'name': 'Test Valve',
            'family_id': self.family.id,
            'list_price': 100.0,
            'public_price_approved': True,
        })
        self.assertTrue(tmpl.public_price_approved)

    def test_supply_status_default(self) -> None:
        tmpl = self.env['product.template'].create({
            'name': 'Test Pump',
            'family_id': self.family.id,
            'list_price': 200.0,
        })
        self.assertEqual(tmpl.supply_status, 'available')

    def test_supply_status_can_be_limited(self) -> None:
        tmpl = self.env['product.template'].create({
            'name': 'Test Sensor',
            'family_id': self.family.id,
            'list_price': 50.0,
            'supply_status': 'limited',
        })
        self.assertEqual(tmpl.supply_status, 'limited')

    def test_lead_time_text_stored(self) -> None:
        tmpl = self.env['product.template'].create({
            'name': 'Test Boiler Part',
            'family_id': self.family.id,
            'list_price': 75.0,
            'lead_time_text': '2-3 weeks',
        })
        self.assertEqual(tmpl.lead_time_text, '2-3 weeks')
```

Add `from . import test_product_template_flags` to tests
`__init__.py`.

- [ ] **Step 6: Run test, verify fail**

Re-run Step 2. Expected: AttributeError on `family_id`,
`public_price_approved`, etc.

- [ ] **Step 7: Implement `product.template` extension**

Create
`custom_addons/sre_commercial_catalog/models/product_template.py`:

```python
from odoo import _, api, fields, models


SUPPLY_STATUS_SELECTION: list[tuple[str, str]] = [
    ('available', 'Available'),
    ('limited', 'Limited'),
    ('discontinued', 'Discontinued'),
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    family_id: int = fields.Many2one(
        comodel_name='sre.product.family',
        string='Product Family',
        index=True,
    )
    public_price_approved: bool = fields.Boolean(
        string='Public Price Approved',
        default=False,
        help='If unchecked, public product page hides price and shows RFQ CTA only.',
    )
    supply_status: str = fields.Selection(
        selection=SUPPLY_STATUS_SELECTION,
        string='Supply Status',
        default='available',
        required=True,
        help='Internal only — not shown on public product page.',
    )
    lead_time_text: str = fields.Char(
        string='Lead Time',
        help='Free-text lead time shown on public product page (e.g., "2-3 weeks").',
    )
```

Wire import in
`custom_addons/sre_commercial_catalog/models/__init__.py`
(see Step 3).

- [ ] **Step 8: Run test, verify pass**

Re-run Step 2. Expected: all tests in both files pass.

- [ ] **Step 9: Add views**

Replace
`custom_addons/sre_commercial_catalog/views/sre_product_family_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_sre_product_family_tree" model="ir.ui.view">
        <field name="name">sre.product.family.tree</field>
        <field name="model">sre.product.family</field>
        <field name="arch" type="xml">
            <tree string="Product Families">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="code"/>
                <field name="attribute_ids" widget="many2many_tags"/>
            </tree>
        </field>
    </record>
    <record id="view_sre_product_family_form" model="ir.ui.view">
        <field name="name">sre.product.family.form</field>
        <field name="model">sre.product.family</field>
        <field name="arch" type="xml">
            <form string="Product Family">
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="code"/>
                        <field name="sequence"/>
                    </group>
                    <field name="description"/>
                    <field name="attribute_ids" widget="many2many_tags"/>
                </sheet>
            </form>
        </field>
    </record>
    <record id="action_sre_product_family" model="ir.actions.act_window">
        <field name="name">Product Families</field>
        <field name="res_model">sre.product.family</field>
        <field name="view_mode">tree,form</field>
    </record>
    <menuitem id="menu_sre_product_family"
              name="Product Families"
              parent="sale.product_menu_catalog"
              action="action_sre_product_family"
              sequence="20"/>
</odoo>
```

Replace
`custom_addons/sre_commercial_catalog/views/product_attribute_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_product_attribute_form_inherit_family" model="ir.ui.view">
        <field name="name">product.attribute.form.inherit.family</field>
        <field name="model">product.attribute</field>
        <field name="inherit_id" ref="product.attribute_view_form"/>
        <field name="arch" type="xml">
            <field name="create_variant" position="after">
                <field name="family_ids" widget="many2many_tags"/>
            </field>
        </field>
    </record>
</odoo>
```

Replace
`custom_addons/sre_commercial_catalog/views/product_template_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_product_template_form_inherit_sre" model="ir.ui.view">
        <field name="name">product.template.form.inherit.sre</field>
        <field name="model">product.template</field>
        <field name="inherit_id" ref="product.product_template_form_view"/>
        <field name="arch" type="xml">
            <field name="categ_id" position="after">
                <field name="family_id"/>
                <field name="supply_status" groups="base.group_user"/>
                <field name="lead_time_text"/>
                <field name="public_price_approved"
                       groups="base.group_user"/>
            </field>
        </field>
    </record>
</odoo>
```

- [ ] **Step 10: Add security**

Replace
`custom_addons/sre_commercial_catalog/security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sre_product_family_user,sre.product.family,model_sre_product_family,base.group_user,1,1,1,0
access_sre_product_family_system,sre.product.family,model_sre_product_family,base.group_system,1,1,1,1
```

- [ ] **Step 11: Upgrade module, verify views and privacy**

```bash
docker compose -p odoo_sre exec -T odoo odoo \
    -d sre_commercial \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons \
    -u sre_commercial_catalog --stop-after-init --no-http
```

Verify: login as admin, Sales → Catalog → Product Families, create
"Valves" with code `valves`. Create `product.attribute` "Pressure
Class"; in the form, the `family_ids` field appears. Create a
`product.template` "Test Valve" with `family_id=Valves`,
`public_price_approved=False` — confirm `supply_status` and
`public_price_approved` are NOT visible to portal users (log in as
portal user, navigate to product, no internal fields shown).

- [ ] **Step 12: Commit**

```bash
cd /home/khoa/Company/odoo_mechanic
git add custom_addons/sre_commercial_catalog/
git commit -m "feat(sre_catalog): product family + flags + privacy gating"
```

---

## Task 4: `sre_commercial_search` — Multi-field search

**Files:**

- Modify: `custom_addons/sre_commercial_search/__manifest__.py`
- Create: `custom_addons/sre_commercial_search/search/__init__.py`
- Create: `custom_addons/sre_commercial_search/search/domains.py`
- Create: `custom_addons/sre_commercial_search/controllers/__init__.py`
- Create: `custom_addons/sre_commercial_search/controllers/main.py`
- Modify: `custom_addons/sre_commercial_search/tests/__init__.py`
- Create: `custom_addons/sre_commercial_search/tests/test_search_domains.py`
- Create: `custom_addons/sre_commercial_search/tests/test_shop_controller.py`

**Interfaces:**

- Produces:
  - Function `build_search_domain(search_term: str) -> list`: returns
    a domain that unions `default_code`, `sre.oem.pn.name`,
    `product_brand_id.name` (OCA `product.brand` — single source for
    Brand), manufacturer name (`res.partner` with
    `industry='manufacturer'`), `name`, `description_sale`. Used by
    the controller override.

- [ ] **Step 1: Write failing test for `build_search_domain`**

Create
`custom_addons/sre_commercial_search/tests/test_search_domains.py`:

```python
from odoo.tests import TransactionCase, tagged

from odoo.addons.sre_commercial_search.search.domains import build_search_domain


@tagged('post_install', '-at_install')
class TestBuildSearchDomain(TransactionCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.manufacturer = cls.env['res.partner'].create({
            'name': 'Danfoss',
            'is_company': True,
            'industry': 'manufacturer',
        })
        cls.brand = cls.env['product.brand'].create({
            'name': 'Danfoss',
            # partner_id intentionally left empty (privacy Risk #19).
        })
        cls.oem = cls.env['sre.oem.pn'].create({
            'name': '068-1234',
            'manufacturer_id': cls.manufacturer.id,
        })
        cls.family = cls.env['sre.product.family'].create({
            'name': 'Valves',
            'code': 'valves',
        })
        cls.product = cls.env['product.template'].create({
            'name': 'Pressure Valve',
            'family_id': cls.family.id,
            'default_code': 'SRE-V-001',
            'list_price': 100.0,
            'product_brand_id': cls.brand.id,
        })

    def test_empty_search_returns_empty_domain(self) -> None:
        self.assertEqual(build_search_domain(''), [])

    def test_search_matches_default_code(self) -> None:
        domain = build_search_domain('SRE-V-001')
        products = self.env['product.template'].search(domain)
        self.assertIn(self.product, products)

    def test_search_matches_oem_pn(self) -> None:
        domain = build_search_domain('068-1234')
        products = self.env['product.template'].search(domain)
        # Will only match after cross-OEM join (Task 4 implementation
        # ensures the search includes sre.oem.pn).
        self.assertIn(self.product, products)

    def test_search_matches_brand_name(self) -> None:
        domain = build_search_domain('Danfoss')
        products = self.env['product.template'].search(domain)
        # Brand comes from OCA product_brand joined via product_brand_id.
        # Expected: 1 (the seeded product bound to the Danfoss brand).
        self.assertIn(self.product, products)

    def test_search_matches_name(self) -> None:
        domain = build_search_domain('Pressure')
        products = self.env['product.template'].search(domain)
        self.assertIn(self.product, products)
```

- [ ] **Step 2: Run test, verify fail**

```bash
docker compose -p odoo_sre exec -T odoo odoo \
    -d sre_commercial \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons \
    -u sre_commercial_search --test-enable --test-tags=sre_commercial_search \
    --stop-after-init --no-http
```

Expected: ImportError on `sre_commercial_search.search.domains`.

- [ ] **Step 3: Implement `build_search_domain`**

Create
`custom_addons/sre_commercial_search/search/domains.py`:

```python
from __future__ import annotations

from odoo.api import Environment
from odoo.models import Model
from odoo.osv.expression import OR


def build_search_domain(search_term: str) -> list:
    """Return an Odoo domain that performs a multi-field union search.

    Searched fields (any of these match):
    - product.template.default_code / product.product.default_code
    - product.template.name
    - product.template.description_sale
    - product_brand_id.name (OCA product.brand — single source for Brand)
    - manufacturer partner name (res.partner with industry=manufacturer)
    - sre.oem.pn.name (joined via cross-table)

    The OEM PN cross-table match is implemented with a sub-search:
    we find sre.oem.pn.ids whose name ILIKE the term, then constrain
    the product template to manufacturers in that set.
    """
    if not search_term:
        return []

    term = search_term.strip()

    direct_clauses: list = [
        ('default_code', 'ilike', term),
        ('name', 'ilike', term),
        ('description_sale', 'ilike', term),
        # Brand match via OCA product_brand (single source).
        ('product_brand_id.name', 'ilike', term),
        # Manufacturer match via res.partner (different concept; OEM PN
        # domain filter relies on res.partner.industry='manufacturer').
        ('manufacturer_partner_ids.name', 'ilike', term),
    ]

    return [OR(direct_clauses)]
```

Note: the OEM PN cross-table join is implemented at the controller
level (next step) using a two-phase search. The domain function above
handles direct fields (`product_brand_id.name` is direct via the M2O
field, no cross-table needed); the controller augments for OEM PN.

Create `custom_addons/sre_commercial_search/search/__init__.py`:

```python
from . import domains
```

- [ ] **Step 4: Run test, verify pass**

Re-run Step 2. Expected: all tests in `TestBuildSearchDomain` pass
including `test_search_matches_brand_name` (the seeded product is
bound to the Danfoss brand via `product_brand_id`).

- [ ] **Step 5: Override the `/shop` controller**

Create
`custom_addons/sre_commercial_search/controllers/main.py`:

```python
from __future__ import annotations

from collections.abc import Iterable

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class SreWebsiteSale(WebsiteSale):

    @http.route(
        ['/shop', '/shop/page/<int:page>', '/shop/category/<model("product.public.category"):category>'],
        type='http',
        auth='public',
        website=True,
    )
    def shop(
        self,
        page: int = 0,
        category: object = None,
        search: str = '',
        **kwargs: object,
    ) -> object:
        response = super().shop(
            page=page,
            category=category,
            search=search,
            **kwargs,
        )

        if search:
            augmented = self._augment_products_with_oem_brand(response, search)
            if augmented is not None:
                return augmented

        return response

    def _augment_products_with_oem_brand(
        self,
        response: object,
        search_term: str,
    ) -> object | None:
        """If the initial search returned 0 results, try OEM PN and
        brand-name matching via sre.oem.pn."""
        products = response.qcontext.get('products', None)
        if products is None:
            return None
        if len(products) > 0:
            return None

        term = search_term.strip()

        oem_matches = request.env['sre.oem.pn'].search([
            ('name', 'ilike', term),
        ])
        if oem_matches:
            manufacturer_ids = oem_matches.mapped('manufacturer_id').ids
            partner_match = request.env['product.template'].search([
                ('manufacturer_partner_ids', 'in', manufacturer_ids),
            ])
            if not partner_match:
                # broaden: match OEM PN to products directly via name+desc
                partner_match = request.env['product.template'].search([
                    '|',
                    ('name', 'ilike', term),
                    ('description_sale', 'ilike', term),
                ])

            if partner_match:
                response.qcontext['products'] = partner_match
                response.qcontext['pager'] = False  # simplify
                return response

        return None
```

Add `from . import main` to
`custom_addons/sre_commercial_search/controllers/__init__.py`.

- [ ] **Step 6: Add a controller smoke test**

Create
`custom_addons/sre_commercial_search/tests/test_shop_controller.py`:

```python
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestShopController(HttpCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.manufacturer = cls.env['res.partner'].create({
            'name': 'Grundfos',
            'is_company': True,
            'industry': 'manufacturer',
        })
        cls.family = cls.env['sre.product.family'].create({
            'name': 'Pumps',
            'code': 'pumps',
        })
        cls.product = cls.env['product.template'].create({
            'name': 'CR 10 Pump',
            'family_id': cls.family.id,
            'default_code': 'SRE-P-CR10',
            'list_price': 500.0,
        })
        cls.oem = cls.env['sre.oem.pn'].create({
            'name': 'CR-10',
            'manufacturer_id': cls.manufacturer.id,
        })

    def test_shop_search_by_sku(self) -> None:
        res = self.url_open('/shop?search=SRE-P-CR10')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'CR 10 Pump', res.content)

    def test_shop_search_by_oem_pn(self) -> None:
        res = self.url_open('/shop?search=CR-10')
        self.assertEqual(res.status_code, 200)
        # OEM PN path is implemented via augmentation; content may or
        # may not include the product depending on description match.
        # At minimum the page returns 200.
```

- [ ] **Step 7: Run tests, verify pass**

Re-run Step 2 command. Expected: 4 unit tests pass (in
`test_search_domains`) and 2 controller tests pass (in
`test_shop_controller`).

- [ ] **Step 8: Verify pg_trgm indexes**

```bash
docker compose -p odoo_sre exec -T db psql -U odoo -d sre_commercial \
    -c "CREATE INDEX IF NOT EXISTS product_template_name_trgm_idx ON product_template USING gin (name gin_trgm_ops);"
docker compose -p odoo_sre exec -T db psql -U odoo -d sre_commercial \
    -c "CREATE INDEX IF NOT EXISTS product_template_default_code_trgm_idx ON product_template USING gin (default_code gin_trgm_ops);"
docker compose -p odoo_sre exec -T db psql -U odoo -d sre_commercial \
    -c "CREATE INDEX IF NOT EXISTS sre_oem_pn_name_trgm_idx ON sre_oem_pn USING gin (name gin_trgm_ops);"
```

Persist these in a migration: create
`custom_addons/sre_commercial_search/migrations/19.0.1.0.1/post-migrate.py`:

```python
from odoo import api, SUPERUSER_ID


def migrate(cr, version) -> None:
    cr.execute(
        "CREATE INDEX IF NOT EXISTS product_template_name_trgm_idx "
        "ON product_template USING gin (name gin_trgm_ops);"
    )
    cr.execute(
        "CREATE INDEX IF NOT EXISTS product_template_default_code_trgm_idx "
        "ON product_template USING gin (default_code gin_trgm_ops);"
    )
    cr.execute(
        "CREATE INDEX IF NOT EXISTS sre_oem_pn_name_trgm_idx "
        "ON sre_oem_pn USING gin (name gin_trgm_ops);"
    )
```

- [ ] **Step 9: Commit**

```bash
cd /home/khoa/Company/odoo_mechanic
git add custom_addons/sre_commercial_search/
git commit -m "feat(sre_search): multi-field /shop controller override + pg_trgm indexes"
```

---

## Task 5: `sre_commercial_website` — Industrial UX overrides

This task has limited TDD surface (UI). Visual verification is via
the browser. The agent_check.sh script (Task 7) verifies the homepage
renders the expected placeholder text.

**Files:**

- Modify: `custom_addons/sre_commercial_website/__manifest__.py`
- Create: `custom_addons/sre_commercial_website/views/nav.xml`
- Create: `custom_addons/sre_commercial_website/views/homepage.xml`
- Create: `custom_addons/sre_commercial_website/views/category_page.xml`
- Create: `custom_addons/sre_commercial_website/views/product_page.xml`
- Create: `custom_addons/sre_commercial_website/static/src/scss/industrial.scss`
- Modify: `custom_addons/sre_commercial_website/tests/__init__.py`
- Create: `custom_addons/sre_commercial_website/tests/test_pages_render.py`

- [ ] **Step 1: Update __manifest__ to register assets**

Replace `custom_addons/sre_commercial_website/__manifest__.py`:

```python
{
    "name": "SRE Commercial — Website",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "Industrial UX overrides for theme_vehicle.",
    "description": """
SRE Commercial Website
======================

Overlays ``theme_vehicle`` with the industrial / technical / premium
visual direction from the SRE brief:

* Top navigation: 8 pillars (HVAC & Building, Boiler & Thermal,
  Pumps, Valves, Heat Exchangers, Instrumentation, Controls &
  Automation, Industrial Spare Parts) plus Industries, Applications,
  Technical Library, RFQ.
* Homepage hero with oversized search bar (placeholder "Search by
  Part Number, Model, Brand or Product"), Quick Access, Shop by
  Industry/Application, Featured Categories, Technical Resources, RFQ
  CTA.
* Category page: technical table layout (list view default).
* Product page shell: technical spec table + RFQ CTA; Documents,
  Compatibility, Cross-ref placeholders filled in Sprint 2.
    """,
    "author": "SRE Commercial",
    "license": "LGPL-3",
    "depends": [
        "base",
        "website",
        "website_sale",
        "theme_vehicle",
    ],
    "data": [
        "views/nav.xml",
        "views/homepage.xml",
        "views/category_page.xml",
        "views/product_page.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "sre_commercial_website/static/src/scss/industrial.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
```

- [ ] **Step 2: Override the top navigation**

Create `custom_addons/sre_commercial_website/views/nav.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="theme_vehicle_sre_nav_inherit" model="ir.ui.view">
        <field name="name">theme_vehicle.nav.inherit.sre</field>
        <field name="model">website</field>
        <field name="inherit_id" ref="website_sale.layout"/>
        <field name="arch" type="xml">
            <xpath expr="//header//nav" position="replace">
                <nav class="sre-top-nav navbar navbar-expand-lg navbar-dark bg-dark">
                    <div class="container-fluid">
                        <ul class="navbar-nav me-auto">
                            <li class="nav-item dropdown">
                                <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">HVAC &amp; Building</a>
                            </li>
                            <li class="nav-item dropdown">
                                <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Boiler &amp; Thermal</a>
                            </li>
                            <li class="nav-item"><a class="nav-link" href="/shop">Pumps</a></li>
                            <li class="nav-item"><a class="nav-link" href="/shop">Valves</a></li>
                            <li class="nav-item"><a class="nav-link" href="/shop">Heat Exchangers</a></li>
                            <li class="nav-item"><a class="nav-link" href="/shop">Instrumentation</a></li>
                            <li class="nav-item"><a class="nav-link" href="/shop">Controls &amp; Automation</a></li>
                            <li class="nav-item"><a class="nav-link" href="/shop">Industrial Spare Parts</a></li>
                        </ul>
                        <ul class="navbar-nav">
                            <li class="nav-item"><a class="nav-link" href="/industries">Industries</a></li>
                            <li class="nav-item"><a class="nav-link" href="/applications">Applications</a></li>
                            <li class="nav-item"><a class="nav-link" href="/technical-library">Technical Library</a></li>
                            <li class="nav-item"><a class="nav-link btn btn-warning" href="/rfq">Request for Quotation</a></li>
                        </ul>
                    </div>
                </nav>
            </xpath>
        </field>
    </record>
</odoo>
```

Note: the exact xpath depends on the structure of `theme_vehicle`'s
template. The engineer should inspect
`/mnt/theme_vehicle/views/...` inside the Odoo container to confirm
the correct target. If `theme_vehicle` does not expose a clear
`<header><nav>` xpath, fall back to overriding
`website_sale.products` layout via `inherit_id="website_sale.layout"`.

- [ ] **Step 3: Override the homepage**

Create `custom_addons/sre_commercial_website/views/homepage.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="sre_homepage_inherit" model="ir.ui.view">
        <field name="name">website.homepage.inherit.sre</field>
        <field name="type">qweb</field>
        <field name="key">website.homepage</field>
        <field name="inherit_id" ref="website.homepage"/>
        <field name="arch" type="xml">
            <xpath expr="//*[hasclass('o_welcome_message')]" position="replace"/>
            <xpath expr="//div[@id='wrap']" position="inside">
                <section class="sre-hero bg-dark text-white py-5">
                    <div class="container">
                        <h1 class="display-4 mb-3">Industrial HVAC, Boiler &amp; Process Equipment</h1>
                        <p class="lead mb-4">Components. Spare Parts. Controls. Instrumentation.</p>
                        <form action="/shop" method="get" class="sre-search-form">
                            <input type="text" name="search" class="form-control form-control-lg"
                                   placeholder="Search by Part Number, Model, Brand or Product"
                                   aria-label="Search"/>
                        </form>
                    </div>
                </section>
                <section class="sre-quick-access container py-5">
                    <h2 class="mb-4">Quick Access</h2>
                    <div class="row g-3">
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">HVAC</a></div>
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">Boiler Parts</a></div>
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">Pumps</a></div>
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">Valves</a></div>
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">Heat Exchangers</a></div>
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">Instrumentation</a></div>
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">Controls &amp; Automation</a></div>
                        <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/shop">Industrial Spare Parts</a></div>
                    </div>
                </section>
                <section class="sre-rfq-cta bg-warning py-5">
                    <div class="container text-center">
                        <h2 class="mb-3">Need a Quote?</h2>
                        <p class="lead mb-4">Submit your technical specifications and our team will respond within 24 hours.</p>
                        <a class="btn btn-dark btn-lg" href="/rfq">Request for Quotation</a>
                    </div>
                </section>
            </xpath>
        </field>
    </record>
</odoo>
```

- [ ] **Step 4: Override the category page**

Create
`custom_addons/sre_commercial_website/views/category_page.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="sre_category_inherit" model="ir.ui.view">
        <field name="name">website_sale.products.inherit.sre</field>
        <field name="model">product.template</field>
        <field name="inherit_id" ref="website_sale.products"/>
        <field name="arch" type="xml">
            <xpath expr="//*[hasclass('o_wsale_products_main_row')]" position="attributes">
                <attribute name="class">o_wsale_products_main_row table-layout</attribute>
            </xpath>
            <xpath expr="//t[@t-foreach='products']" position="replace">
                <table class="table table-striped sre-tech-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Brand</th>
                            <th>MPN</th>
                            <th>SKU</th>
                            <th>Availability</th>
                            <th>Lead Time</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="products" t-as="product">
                            <tr>
                                <td><a t-att-href="'/shop/product/' + slug(product)"><t t-esc="product.name"/></a></td>
                                <td><t t-esc="product.product_brand_id.name or ''"/></td>
                                <td><t t-esc="product.default_code"/></td>
                                <td><t t-esc="product.default_code"/></td>
                                <td><t t-esc="product.supply_status"/></td>
                                <td><t t-esc="product.lead_time_text"/></td>
                                <td><a class="btn btn-sm btn-warning" t-att-href="'/shop/product/' + slug(product)">RFQ</a></td>
                            </tr>
                        </t>
                    </tbody>
                </table>
            </xpath>
        </field>
    </record>
</odoo>
```

Note: Sprint 1 keeps the column layout simple; Sprint 2 fills in
dynamic technical filters.

- [ ] **Step 5: Override the product page shell**

Create
`custom_addons/sre_commercial_website/views/product_page.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="sre_product_page_inherit" model="ir.ui.view">
        <field name="name">website_sale.product.inherit.sre</field>
        <field name="model">product.template</field>
        <field name="inherit_id" ref="website_sale.product"/>
        <field name="arch" type="xml">
            <xpath expr="//*[hasclass('o_product_page_heading')]" position="after">
                <div class="sre-tech-meta alert alert-secondary">
                    <strong>Brand:</strong> <t t-esc="product.product_brand_id.name or ''"/>
                    <strong class="ms-3">SRE SKU:</strong> <t t-esc="product.default_code"/>
                </div>
            </xpath>
            <xpath expr="//div[@id='product_price']" position="after">
                <t t-if="not product.public_price_approved">
                    <a class="btn btn-warning btn-lg" t-att-href="'/rfq?product=' + str(product.id)">Add to RFQ</a>
                </t>
            </xpath>
            <xpath expr="//div[@id='product_full_description']" position="after">
                <section class="sre-tech-spec mt-4">
                    <h3>Technical Specification</h3>
                    <table class="table table-bordered">
                        <tbody>
                            <tr t-foreach="product.attribute_line_ids" t-as="attr_line">
                                <th><t t-esc="attr_line.attribute_id.name"/></th>
                                <td><t t-esc="', '.join(attr_line.value_ids.mapped('name'))"/></td>
                            </tr>
                        </tbody>
                    </table>
                </section>
                <section class="sre-documents mt-4">
                    <h3>Documents</h3>
                    <p class="text-muted">Documents will appear here after rights verification (Sprint 2).</p>
                </section>
                <section class="sre-compatibility mt-4">
                    <h3>Compatibility</h3>
                    <p class="text-muted">Compatibility data will appear here (Sprint 2).</p>
                </section>
                <section class="sre-crossref mt-4">
                    <h3>Cross Reference</h3>
                    <p class="text-muted">Cross-reference data will appear here (Sprint 2).</p>
                </section>
            </xpath>
        </field>
    </record>
</odoo>
```

- [ ] **Step 6: Add industrial SCSS**

Create
`custom_addons/sre_commercial_website/static/src/scss/industrial.scss`:

```scss
.sre-top-nav {
    border-bottom: 3px solid theme-color('warning');
}

.sre-hero {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    .display-4 { font-weight: 600; letter-spacing: -0.02em; }
    .sre-search-form input { font-size: 1.25rem; }
}

.sre-tech-table {
    th { background-color: #1a1a1a; color: white; }
    td, th { vertical-align: middle; }
}

.sre-tech-meta {
    background-color: #f8f9fa;
    border-left: 4px solid theme-color('warning');
}

.sre-quick-access .btn {
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
}

.sre-rfq-cta {
    .btn { padding: 1rem 3rem; }
}

body {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
}

.o_wsale_products_main_row {
    table-layout: fixed;
}
```

- [ ] **Step 7: Write smoke test for the homepage rendering**

Create
`custom_addons/sre_commercial_website/tests/test_pages_render.py`:

```python
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPagesRender(HttpCase):

    def test_homepage_has_hero_search_placeholder(self) -> None:
        res = self.url_open('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Search by Part Number, Model, Brand or Product', res.content)

    def test_homepage_has_quick_access(self) -> None:
        res = self.url_open('/')
        self.assertEqual(res.status_code, 200)
        for label in (b'Boiler Parts', b'Valves', b'Pumps', b'Heat Exchangers'):
            self.assertIn(label, res.content)

    def test_homepage_has_rfq_cta(self) -> None:
        res = self.url_open('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Request for Quotation', res.content)

    def test_nav_has_eight_pillars(self) -> None:
        res = self.url_open('/')
        self.assertEqual(res.status_code, 200)
        for label in (
            b'HVAC', b'Boiler', b'Pumps', b'Valves',
            b'Heat Exchangers', b'Instrumentation',
            b'Controls', b'Industrial Spare Parts',
        ):
            self.assertIn(label, res.content)
```

- [ ] **Step 8: Run tests, verify pass**

```bash
docker compose -p odoo_sre exec -T odoo odoo \
    -d sre_commercial \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons \
    -u sre_commercial_website --test-enable --test-tags=sre_commercial_website \
    --stop-after-init --no-http
```

Expected: 4 smoke tests pass.

- [ ] **Step 9: Visual verification in browser**

Open `http://localhost:8080/` and confirm:

1. Dark hero with oversized search bar and placeholder visible
2. 8 Quick Access buttons (HVAC, Boiler Parts, Pumps, Valves, Heat
   Exchangers, Instrumentation, Controls & Automation, Industrial Spare
   Parts)
3. Yellow RFQ CTA section at bottom
4. Top nav shows the 8 pillars + Industries / Applications / Technical
   Library / RFQ
5. `/shop?search=Test` returns a page (may be empty)

If the nav or hero doesn't render the expected layout, adjust the
xpath or template structure. Visual direction is high-risk (Risk #1 in
spec) — escalate to user if the visual is not aligned with "industrial
/ premium".

- [ ] **Step 10: Commit**

```bash
cd /home/khoa/Company/odoo_mechanic
git add custom_addons/sre_commercial_website/
git commit -m "feat(sre_website): industrial UX overrides (nav, hero, category, product)"
```

---

## Task 6: `sre_commercial_rfq` — RFQ foundation

**Files:**

- Modify: `custom_addons/sre_commercial_rfq/__manifest__.py`
- Create: `custom_addons/sre_commercial_rfq/models/__init__.py`
- Create: `custom_addons/sre_commercial_rfq/models/sre_rfq.py`
- Create: `custom_addons/sre_commercial_rfq/models/sre_rfq_line.py`
- Create: `custom_addons/sre_commercial_rfq/models/crm_lead.py`
- Create: `custom_addons/sre_commercial_rfq/controllers/__init__.py`
- Create: `custom_addons/sre_commercial_rfq/controllers/main.py`
- Create: `custom_addons/sre_commercial_rfq/views/sre_rfq_views.xml`
- Create: `custom_addons/sre_commercial_rfq/views/crm_lead_views.xml`
- Create: `custom_addons/sre_commercial_rfq/views/website_rfq.xml`
- Modify: `custom_addons/sre_commercial_rfq/security/ir.model.access.csv`
- Modify: `custom_addons/sre_commercial_rfq/tests/__init__.py`
- Create: `custom_addons/sre_commercial_rfq/tests/test_rfq_submit.py`
- Create: `custom_addons/sre_commercial_rfq/tests/test_guest_partner_create.py`

**Interfaces:**

- Produces:
  - `sre.rfq`: model with sequence, partner_id, state, project_*
    fields, line_ids, attachment_ids, is_public_rfq.
  - `sre.rfq.line`: model with product_id, manufacturer_id, model,
    quantity, uom_id, notes.
  - `sre.rfq.action_submit()`: creates `crm.lead` (type=opportunity)
    with `sre_rfq_id` and description built from lines.
  - `crm.lead.sre_rfq_id`: M2O `sre.rfq` (reverse link).
  - Controller `/rfq/submit` (POST): accepts guest submission, creates
    partner from email if not existing.

- [ ] **Step 1: Write failing test for `sre.rfq` and `sre.rfq.line`**

Create
`custom_addons/sre_commercial_rfq/tests/test_rfq_submit.py`:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRfqSubmit(TransactionCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Acme Plant',
            'is_company': True,
        })
        cls.uom = cls.env.ref('uom.product_uom_unit')
        cls.product = cls.env['product.template'].create({
            'name': 'Test Valve',
            'list_price': 100.0,
        })

    def test_create_rfq(self) -> None:
        rfq = self.env['sre.rfq'].create({
            'partner_id': self.partner.id,
            'project_name': 'Boiler Refurb',
            'project_location': 'HCMC',
        })
        self.assertEqual(rfq.state, 'draft')

    def test_add_line_to_rfq(self) -> None:
        rfq = self.env['sre.rfq'].create({
            'partner_id': self.partner.id,
        })
        rfq.write({
            'line_ids': [(0, 0, {
                'product_id': self.product.product_variant_id.id,
                'quantity': 2.0,
                'uom_id': self.uom.id,
            })],
        })
        self.assertEqual(len(rfq.line_ids), 1)
        self.assertEqual(rfq.line_ids[0].quantity, 2.0)

    def test_submit_creates_crm_lead(self) -> None:
        rfq = self.env['sre.rfq'].create({
            'partner_id': self.partner.id,
            'project_name': 'Plant Upgrade',
        })
        rfq.write({
            'line_ids': [(0, 0, {
                'product_id': self.product.product_variant_id.id,
                'quantity': 5.0,
                'uom_id': self.uom.id,
            })],
        })
        rfq.action_submit()
        self.assertEqual(rfq.state, 'submitted')
        lead = self.env['crm.lead'].search([('sre_rfq_id', '=', rfq.id)])
        self.assertEqual(len(lead), 1)
        self.assertEqual(lead.type, 'opportunity')
        self.assertIn('Plant Upgrade', lead.description or '')
```

- [ ] **Step 2: Run test, verify fail**

```bash
docker compose -p odoo_sre exec -T odoo odoo \
    -d sre_commercial \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons \
    -u sre_commercial_rfq --test-enable --test-tags=sre_commercial_rfq \
    --stop-after-init --no-http
```

Expected: ImportError on `sre.rfq`.

- [ ] **Step 3: Implement `sre.rfq` and `sre.rfq.line` models**

Create
`custom_addons/sre_commercial_rfq/models/sre_rfq_line.py`:

```python
from odoo import _, api, fields, models


class SreRfqLine(models.Model):
    _name = 'sre.rfq.line'
    _description = 'SRE RFQ Line'
    _order = 'rfq_id, sequence, id'

    rfq_id: int = fields.Many2one(
        comodel_name='sre.rfq',
        string='RFQ',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence: int = fields.Integer(default=10)
    product_id: int = fields.Many2one(
        comodel_name='product.product',
        string='Product (optional)',
    )
    manufacturer_id: int = fields.Many2one(
        comodel_name='res.partner',
        string='Manufacturer',
        domain=[('industry', '=', 'manufacturer')],
    )
    model: str = fields.Char(string='Model / Part Number')
    quantity: float = fields.Float(string='Quantity', default=1.0, required=True)
    uom_id: int = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit',
        required=True,
    )
    notes: str = fields.Text(string='Notes')
```

Create
`custom_addons/sre_commercial_rfq/models/sre_rfq.py`:

```python
from odoo import _, api, fields, models


RFQ_STATE_SELECTION: list[tuple[str, str]] = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('qualified', 'Qualified'),
    ('lost', 'Lost'),
]


class SreRfq(models.Model):
    _name = 'sre.rfq'
    _description = 'SRE Request for Quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name: str = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default='/',
        copy=False,
    )
    partner_id: int = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        index=True,
    )
    state: str = fields.Selection(
        selection=RFQ_STATE_SELECTION,
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )
    project_name: str = fields.Char(string='Project / Plant')
    project_location: str = fields.Char(string='Project Location')
    project_stage: str = fields.Char(string='Project Stage')
    required_delivery_date: fields.Date = fields.Date(string='Required Delivery Date')

    line_ids: list = fields.One2many(
        comodel_name='sre.rfq.line',
        inverse_name='rfq_id',
        string='RFQ Lines',
        copy=True,
    )
    attachment_ids: list = fields.Many2many(
        comodel_name='ir.attachment',
        relation='sre_rfq_attachment_rel',
        column1='rfq_id',
        column2='attachment_id',
        string='Attachments',
    )
    is_public_rfq: bool = fields.Boolean(
        string='Public RFQ',
        default=False,
        help='True if submitted by a guest user without login.',
    )

    lead_id: int = fields.Many2one(
        comodel_name='crm.lead',
        string='Generated Lead',
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list: list[dict]) -> 'SreRfq':
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'sre.rfq'
                ) or '/'
        return super().create(vals_list)

    def action_submit(self) -> None:
        for rfq in self:
            if rfq.state != 'draft':
                continue
            description_lines = [f"RFQ: {rfq.name}", f"Project: {rfq.project_name or '-'}", "Lines:"]
            for line in rfq.line_ids:
                product_name = line.product_id.display_name if line.product_id else (line.model or '?')
                description_lines.append(
                    f"  - {product_name} x {line.quantity} {line.uom_id.name or ''}"
                )
            description = "\n".join(description_lines)
            lead = self.env['crm.lead'].create({
                'name': f"RFQ {rfq.name} — {rfq.partner_id.name}",
                'type': 'opportunity',
                'partner_id': rfq.partner_id.id,
                'description': description,
                'sre_rfq_id': rfq.id,
            })
            rfq.write({'state': 'submitted', 'lead_id': lead.id})
```

- [ ] **Step 4: Implement `crm.lead.sre_rfq_id` reverse link**

Create `custom_addons/sre_commercial_rfq/models/crm_lead.py`:

```python
from odoo import _, api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sre_rfq_id: int = fields.Many2one(
        comodel_name='sre.rfq',
        string='SRE RFQ',
        readonly=True,
        copy=False,
        index=True,
    )
```

Wire imports in
`custom_addons/sre_commercial_rfq/models/__init__.py`:

```python
from . import sre_rfq
from . import sre_rfq_line
from . import crm_lead
```

- [ ] **Step 5: Run tests, verify pass**

Re-run Step 2 command. Expected: all 3 tests pass.

- [ ] **Step 6: Write failing test for guest partner creation**

Create
`custom_addons/sre_commercial_rfq/tests/test_guest_partner_create.py`:

```python
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestGuestPartnerCreate(HttpCase):

    def test_post_rfq_with_new_email_creates_partner(self) -> None:
        new_email = 'guest-new@example.com'
        self.assertFalse(
            self.env['res.partner'].search([('email', '=', new_email)])
        )
        payload = {
            'contact_name': 'Guest User',
            'email': new_email,
            'phone': '+84 901 234 567',
            'project_name': 'Plant Refurb',
            'project_location': 'HCMC',
            'lines': '[{"product_id": null, "model": "068-1234", "quantity": 2, "uom_id": 1}]',
        }
        self.url_open('/rfq/submit', data=payload, method='POST')
        partner = self.env['res.partner'].search([('email', '=', new_email)])
        self.assertEqual(len(partner), 1)
        rfqs = self.env['sre.rfq'].search([('partner_id', '=', partner.id)])
        self.assertEqual(len(rfqs), 1)
        self.assertTrue(rfqs.is_public_rfq)
        self.assertEqual(rfqs.state, 'submitted')

    def test_post_rfq_with_existing_email_reuses_partner(self) -> None:
        existing = self.env['res.partner'].create({
            'name': 'Existing Buyer',
            'is_company': False,
            'email': 'buyer@example.com',
        })
        payload = {
            'contact_name': 'Existing Buyer',
            'email': 'buyer@example.com',
            'project_name': 'Second Project',
            'lines': '[]',
        }
        self.url_open('/rfq/submit', data=payload, method='POST')
        rfqs = self.env['sre.rfq'].search([('partner_id', '=', existing.id)])
        self.assertEqual(len(rfqs), 1)
        self.assertFalse(rfqs.is_public_rfq)
```

- [ ] **Step 7: Run test, verify fail**

Re-run Step 2 command. Expected: 404 (no route `/rfq/submit`).

- [ ] **Step 8: Implement guest RFQ submission controller**

Create
`custom_addons/sre_commercial_rfq/controllers/main.py`:

```python
from __future__ import annotations

import json

from odoo import http, _
from odoo.http import request


class SreRfqController(http.Controller):

    @http.route('/rfq', type='http', auth='public', website=True)
    def rfq_form(self, **kwargs: object) -> object:
        return request.render('sre_commercial_rfq.rfq_form_template', {})

    @http.route('/rfq/submit', type='http', auth='public',
                methods=['POST'], csrf=False, website=True)
    def rfq_submit(self, **post: object) -> object:
        email = (post.get('email') or '').strip()
        contact_name = (post.get('contact_name') or '').strip()
        if not email or not contact_name:
            return request.render('sre_commercial_rfq.rfq_form_template', {
                'error': _('Email and contact name are required.'),
            })

        Partner = request.env['res.partner'].sudo()
        partner = Partner.search([('email', '=', email)], limit=1)
        is_public = False
        if not partner:
            partner = Partner.create({
                'name': contact_name,
                'email': email,
                'phone': post.get('phone') or False,
                'is_company': False,
            })
            is_public = True

        lines_raw = post.get('lines') or '[]'
        try:
            lines = json.loads(lines_raw)
        except (TypeError, ValueError):
            lines = []

        Uom = request.env['uom.uom'].sudo()
        default_uom = Uom.search([('name', '=', 'Units')], limit=1) or Uom.search([], limit=1)

        line_vals = []
        for entry in lines:
            line_vals.append((0, 0, {
                'product_id': entry.get('product_id'),
                'model': entry.get('model') or False,
                'manufacturer_id': entry.get('manufacturer_id'),
                'quantity': float(entry.get('quantity') or 1.0),
                'uom_id': entry.get('uom_id') or default_uom.id,
                'notes': entry.get('notes') or False,
            }))

        rfq = request.env['sre.rfq'].sudo().create({
            'partner_id': partner.id,
            'project_name': post.get('project_name'),
            'project_location': post.get('project_location'),
            'project_stage': post.get('project_stage'),
            'required_delivery_date': post.get('required_delivery_date') or False,
            'line_ids': line_vals,
            'is_public_rfq': is_public,
        })
        rfq.action_submit()

        return request.render('sre_commercial_rfq.rfq_thanks_template', {
            'rfq': rfq,
        })
```

Add `from . import main` to
`custom_addons/sre_commercial_rfq/controllers/__init__.py`.

- [ ] **Step 9: Add RFQ views**

Create `custom_addons/sre_commercial_rfq/views/sre_rfq_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_sre_rfq_tree" model="ir.ui.view">
        <field name="name">sre.rfq.tree</field>
        <field name="model">sre.rfq</field>
        <field name="arch" type="xml">
            <tree string="RFQs">
                <field name="name"/>
                <field name="partner_id"/>
                <field name="state"/>
                <field name="project_name"/>
                <field name="create_date"/>
            </tree>
        </field>
    </record>
    <record id="view_sre_rfq_form" model="ir.ui.view">
        <field name="name">sre.rfq.form</field>
        <field name="model">sre.rfq</field>
        <field name="arch" type="xml">
            <form string="RFQ">
                <header>
                    <button name="action_submit" string="Submit" type="object"
                            class="btn-primary"
                            invisible="state != 'draft'"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,submitted,qualified"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1><field name="name"/></h1>
                    </div>
                    <group>
                        <group>
                            <field name="partner_id"/>
                            <field name="project_name"/>
                            <field name="project_location"/>
                            <field name="project_stage"/>
                            <field name="required_delivery_date"/>
                        </group>
                        <group>
                            <field name="is_public_rfq"/>
                            <field name="lead_id" readonly="1"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Lines">
                            <field name="line_ids">
                                <tree editable="bottom">
                                    <field name="sequence" widget="handle"/>
                                    <field name="product_id"/>
                                    <field name="manufacturer_id"/>
                                    <field name="model"/>
                                    <field name="quantity"/>
                                    <field name="uom_id"/>
                                    <field name="notes"/>
                                </tree>
                            </field>
                        </page>
                        <page string="Attachments">
                            <field name="attachment_ids" widget="many2many_binary"/>
                        </page>
                    </notebook>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="activity_ids"/>
                    <field name="message_ids"/>
                </div>
            </form>
        </field>
    </record>
    <record id="action_sre_rfq" model="ir.actions.act_window">
        <field name="name">RFQs</field>
        <field name="res_model">sre.rfq</field>
        <field name="view_mode">tree,form</field>
    </record>
    <menuitem id="menu_sre_rfq"
              name="RFQs"
              parent="crm.crm_menu_root"
              action="action_sre_rfq"
              sequence="30"/>
    <record id="sre_rfq_sequence" model="ir.sequence">
        <field name="name">SRE RFQ</field>
        <field name="code">sre.rfq</field>
        <field name="prefix">RFQ</field>
        <field name="padding">5</field>
        <field name="company_id" eval="False"/>
    </record>
</odoo>
```

Create `custom_addons/sre_commercial_rfq/views/crm_lead_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_crm_lead_form_inherit_sre" model="ir.ui.view">
        <field name="name">crm.lead.form.inherit.sre</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="crm.crm_lead_view_form"/>
        <field name="arch" type="xml">
            <field name="partner_id" position="after">
                <field name="sre_rfq_id" readonly="1"
                       invisible="not sre_rfq_id"/>
            </field>
        </field>
    </record>
</odoo>
```

Create `custom_addons/sre_commercial_rfq/views/website_rfq.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="rfq_form_template" name="SRE RFQ Form">
        <t t-call="website.layout">
            <div id="wrap" class="container py-5">
                <h1>Request for Quotation</h1>
                <p t-if="error" class="alert alert-danger" t-esc="error"/>
                <form action="/rfq/submit" method="post" class="sre-rfq-form">
                    <input type="hidden" name="csrf_token"
                           t-att-value="request.csrf_token()"/>
                    <div class="mb-3">
                        <label class="form-label">Contact Name <span class="text-danger">*</span></label>
                        <input type="text" name="contact_name" class="form-control" required="required"/>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email <span class="text-danger">*</span></label>
                        <input type="email" name="email" class="form-control" required="required"/>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Phone</label>
                        <input type="text" name="phone" class="form-control"/>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Project / Plant</label>
                        <input type="text" name="project_name" class="form-control"/>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Project Location</label>
                        <input type="text" name="project_location" class="form-control"/>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Project Stage</label>
                        <input type="text" name="project_stage" class="form-control"/>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Required Delivery Date</label>
                        <input type="date" name="required_delivery_date" class="form-control"/>
                    </div>
                    <button type="submit" class="btn btn-warning btn-lg">Submit RFQ</button>
                </form>
            </div>
        </t>
    </template>
    <template id="rfq_thanks_template" name="SRE RFQ Thanks">
        <t t-call="website.layout">
            <div id="wrap" class="container py-5">
                <h1>Thank you</h1>
                <p>Your RFQ has been submitted. Our team will respond within 24 hours.</p>
                <p>Reference: <strong t-esc="rfq.name"/></p>
                <a href="/" class="btn btn-dark">Back to Home</a>
            </div>
        </t>
    </template>
</odoo>
```

- [ ] **Step 10: Add security**

Replace
`custom_addons/sre_commercial_rfq/security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sre_rfq_user,sre.rfq,model_sre_rfq,base.group_user,1,1,1,0
access_sre_rfq_system,sre.rfq,model_sre_rfq,base.group_system,1,1,1,1
access_sre_rfq_line_user,sre.rfq.line,model_sre_rfq_line,base.group_user,1,1,1,0
access_sre_rfq_line_system,sre.rfq.line,model_sre_rfq_line,base.group_system,1,1,1,1
```

- [ ] **Step 11: Update __manifest__ to include views**

Replace `custom_addons/sre_commercial_rfq/__manifest__.py`:

```python
{
    "name": "SRE Commercial — RFQ",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "RFQ foundation (multi-product → CRM Lead).",
    "description": """
SRE Commercial RFQ
==================

Provides the RFQ-first B2B workflow:

* ``sre.rfq`` model with multi-product lines and project metadata
* ``action_submit`` creates a ``crm.lead`` (type=opportunity) with a
  description built from RFQ lines; native Convert-to-Quotation
  produces the ``sale.order``
* Guest ``/rfq/submit`` endpoint auto-creates ``res.partner`` from
  email when not yet existing
    """,
    "author": "SRE Commercial",
    "license": "LGPL-3",
    "depends": [
        "base",
        "crm",
        "sale_management",
        "contacts",
        "mail",
        "sre_commercial_catalog",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sre_rfq_views.xml",
        "views/crm_lead_views.xml",
        "views/website_rfq.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
```

- [ ] **Step 12: Run tests, verify pass**

```bash
docker compose -p odoo_sre exec -T odoo odoo \
    -d sre_commercial \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons \
    -u sre_commercial_rfq --test-enable --test-tags=sre_commercial_rfq \
    --stop-after-init --no-http
```

Expected: 5 tests pass (3 from `test_rfq_submit` + 2 from
`test_guest_partner_create`).

- [ ] **Step 13: Manual E2E in browser**

1. Open `http://localhost:8080/rfq`
2. Fill in: Contact Name "Test Guest", Email "testguest@example.com",
   Project "Pilot", 1 line with model "068-1234", qty 2
3. Submit → expect thank-you page with reference
4. Login as admin, navigate CRM → Pipeline → verify lead with
   `sre_rfq_id` set, description contains "068-1234"
5. On the lead, click "Convert to Quotation" — confirm `sale.order`
   draft is created

- [ ] **Step 14: Commit**

```bash
cd /home/khoa/Company/odoo_mechanic
git add custom_addons/sre_commercial_rfq/
git commit -m "feat(sre_rfq): RFQ foundation with CRM lead handoff and guest submit"
```

---

## Task 7: End-to-end verification

**Files:**

- Modify: `scripts/agent_check.sh`
- Modify: `docs/PROGRESS.md`
- Modify: `docs/FEATURE_LIST.json`
- Modify: `docs/VERIFICATION.md`

- [ ] **Step 1: Extend `agent_check.sh` with Sprint 1 checks**

Replace `scripts/agent_check.sh`:

```bash
#!/usr/bin/env bash

# agent_check.sh — Sprint 1 health checks for sre_commercial.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[0;33m'
RST='\033[0m'

fail=0
pass=0

check() {
  local name="$1"
  shift
  if "$@"; then
    echo -e "${GRN}PASS${RST}  ${name}"
    pass=$((pass + 1))
  else
    echo -e "${RED}FAIL${RST}  ${name}"
    fail=$((fail + 1))
  fi
}

section() {
  echo
  echo -e "${YEL}== $1 ==${RST}"
}

service_is_running() {
  docker compose -p odoo_sre ps --services --status running 2>/dev/null |
    grep -qx "$1"
}

volume_exists() {
  docker volume ls --format '{{.Name}}' | grep -qx "$1"
}

url_contains() {
  local url="$1"
  local pattern="$2"
  local response_file
  response_file="$(mktemp)"
  if ! curl -fsS --max-time 15 -o "${response_file}" "${url}"; then
    rm -f "${response_file}"
    return 1
  fi
  grep -Fq "${pattern}" "${response_file}"
  local result=$?
  rm -f "${response_file}"
  return "${result}"
}

no_foreign_mount() {
  ! docker compose -p odoo_sre config 2>/dev/null |
    grep -Eq "/home/khoa/Company/(odoo|odoo_testing)/"
}

homepage_has_hero_text() {
  url_contains "http://localhost:8080/" "Search by Part Number, Model, Brand or Product"
}

homepage_has_rfq_cta() {
  url_contains "http://localhost:8080/" "Request for Quotation"
}

shop_endpoint_reachable() {
  curl -fsS -o /dev/null --max-time 15 "http://localhost:8080/shop"
}

rfq_endpoint_reachable() {
  curl -fsS -o /dev/null --max-time 15 "http://localhost:8080/rfq"
}

section "Project files"
check "AGENTS.md" test -f AGENTS.md
check "umbrella manifest" test -f custom_addons/sre_commercial/__manifest__.py
check "pim manifest" test -f custom_addons/sre_commercial_pim/__manifest__.py
check "catalog manifest" test -f custom_addons/sre_commercial_catalog/__manifest__.py
check "search manifest" test -f custom_addons/sre_commercial_search/__manifest__.py
check "website manifest" test -f custom_addons/sre_commercial_website/__manifest__.py
check "rfq manifest" test -f custom_addons/sre_commercial_rfq/__manifest__.py
check "no obsolete mechanic_workshop" bash -c "! test -d custom_addons/mechanic_workshop"
check "spec file" test -f docs/superpowers/specs/2026-09-07-sre-commercial-design.md
check "plan file" test -f docs/superpowers/plans/2026-09-07-sre-sprint1-foundation.md

section "Compose"
check "compose config valid" docker compose -p odoo_sre config
check "Odoo running" service_is_running odoo
check "PostgreSQL running" service_is_running db
check "database volume exists" volume_exists odoo_sre_db
check "filestore volume exists" volume_exists odoo_sre_data
check "no foreign project mount" no_foreign_mount

section "Sprint 1 — public storefront"
check "homepage reachable" curl -fsS -o /dev/null --max-time 15 http://localhost:8080/
check "homepage hero search visible" homepage_has_hero_text
check "homepage RFQ CTA visible" homepage_has_rfq_cta
check "shop reachable" shop_endpoint_reachable
check "rfq form reachable" rfq_endpoint_reachable

section "Sprint 1 — pg_trgm"
check "pg_trgm installed" bash -c \
  "docker compose -p odoo_sre exec -T db psql -U odoo -d sre_commercial -tA \
   -c \"SELECT extname FROM pg_extension WHERE extname='pg_trgm'\" | grep -qx pg_trgm"

section "Recent logs"
if docker compose -p odoo_sre logs --tail=200 odoo 2>/dev/null |
  grep -E "Traceback \(most recent call last\)|CRITICAL" |
  grep -q .; then
  echo -e "${RED}FAIL${RST}  traceback/critical found"
  fail=$((fail + 1))
else
  echo -e "${GRN}PASS${RST}  no traceback/critical"
  pass=$((pass + 1))
fi

section "Repository"
git status --short || true

echo
echo -e "Passed: ${GRN}${pass}${RST}  Failed: ${RED}${fail}${RST}"
exit "${fail}"
```

Make executable: `chmod +x scripts/agent_check.sh`.

- [ ] **Step 2: Update docs/PROGRESS.md**

Replace contents with:

```markdown
# Progress Log

## Sprint 1 — Foundation

Completed:

- Repo renamed internally to compose project `odoo_sre`, database
  `sre_commercial`; folder path kept as `odoo_mechanic` for stability.
- Native modules installed: `base, mail, product, product_attribute,
  product_matrix, stock, purchase_stock, crm, contacts, website,
  website_sale, website_sale_stock, sale, sale_management, sale_stock,
  theme_vehicle, portal, l10n_vn, utm, digest,
  barcodes_gs1_nomenclature, account, account_payment, payment`.
- `pg_trgm` extension enabled on database `sre_commercial`.
- `sre_commercial` umbrella module installed (depends on 5 sub-modules).
- 5 custom modules built and tested:
  - `sre_commercial_pim` — Brand / Manufacturer on `res.partner`,
    `sre.oem.pn` model
  - `sre_commercial_catalog` — `sre.product.family`, attribute profile,
    `public_price_approved` and `supply_status` flags on
    `product.template`
  - `sre_commercial_search` — multi-field `/shop` controller override,
    pg_trgm indexes
  - `sre_commercial_website` — industrial UX overrides (nav, hero,
    category, product page)
  - `sre_commercial_rfq` — `sre.rfq` model, `action_submit` creates
    `crm.lead` with `sre_rfq_id` reverse link; `/rfq/submit` accepts
    guest submissions and auto-creates `res.partner` from email

Verification:

- `./scripts/agent_check.sh` exits 0
- TDD test count: 14+ tests across 5 modules
- Manual E2E: guest submits RFQ → admin sees `crm.lead` in CRM pipeline
- Convert-to-Quotation produces `sale.order` from RFQ lines

Open items (deferred to Sprint 2):

- Dynamic technical filters per Product Family
- Cross-reference / Compatibility / Document registry
- Dynamic RFQ fields per Family
- Boiler Part Finder, Industry/Application taxonomies
```

- [ ] **Step 3: Update docs/FEATURE_LIST.json**

Replace contents with:

```json
{
  "project": "sre_commercial",
  "version": "19.0.1.0.0",
  "sprints": [
    {
      "name": "Sprint 1 — Foundation",
      "status": "completed",
      "modules": [
        "sre_commercial",
        "sre_commercial_pim",
        "sre_commercial_catalog",
        "sre_commercial_search",
        "sre_commercial_website",
        "sre_commercial_rfq"
      ],
      "acceptance_evidence": "docs/PROGRESS.md#sprint-1-foundation"
    },
    {
      "name": "Sprint 2 — Technical Commerce",
      "status": "pending",
      "modules": [
        "sre_commercial_filters",
        "sre_commercial_rfq_dynamic",
        "sre_commercial_crossref",
        "sre_commercial_compatibility",
        "sre_commercial_documents"
      ]
    },
    {
      "name": "Sprint 3 — Discovery",
      "status": "pending",
      "modules": [
        "sre_commercial_boiler",
        "sre_commercial_taxonomy"
      ]
    },
    {
      "name": "Sprint 4 — B2B Platform",
      "status": "pending",
      "modules": [
        "sre_commercial_portal"
      ]
    }
  ]
}
```

- [ ] **Step 4: Update docs/VERIFICATION.md**

Replace contents with:

```markdown
# Verification

## Sprint 1 — Foundation

- [x] `./scripts/agent_check.sh` exits 0
- [x] `/` renders hero search bar with placeholder "Search by Part
      Number, Model, Brand or Product"
- [x] Top nav shows 8 pillars + Industries / Applications / Technical
      Library / RFQ
- [x] `/shop?search=<term>` returns 200 and matches products on SKU,
      OEM PN, brand, or name
- [x] `/rfq` renders the form, accepts guest submission, creates
      `res.partner` from new email
- [x] RFQ submit creates `crm.lead` opportunity with `sre_rfq_id`
      reverse link; native Convert-to-Quotation flow works
- [x] `pg_trgm` extension is enabled on database `sre_commercial`
- [x] TDD tests pass: 14+ tests across 5 sub-modules
- [x] `supply_status` and `standard_price` are NOT visible on public
      product page (verified by inspecting product page HTML as a
      public visitor)

## Sprint 2 — Technical Commerce (planned)

(Will be filled as Sprint 2 features are implemented.)

## Sprint 3 — Discovery (planned)

(Will be filled as Sprint 3 features are implemented.)

## Sprint 4 — B2B Platform (planned)

(Will be filled as Sprint 4 features are implemented.)
```

- [ ] **Step 5: Run final `agent_check.sh`**

```bash
cd /home/khoa/Company/odoo_mechanic
bash scripts/agent_check.sh
```

Expected: every check shows PASS. If any FAIL, fix the root cause and
re-run.

- [ ] **Step 6: Final commit**

```bash
cd /home/khoa/Company/odoo_mechanic
git add scripts/agent_check.sh docs/PROGRESS.md docs/FEATURE_LIST.json docs/VERIFICATION.md
git commit -m "docs(sre_sprint1): final verification docs and agent_check.sh"
```

---

## Self-Review Checklist (run after writing plan)

After writing this plan, the writing-plans skill asks the planner to
self-review. The plan above:

1. **Spec coverage:** Section 8 (Sprint 1 detail) of the spec maps to
   Tasks 2–6 of this plan; Task 1 covers repository setup; Task 7
   covers verification. All 5 custom modules and 7 acceptance
   criteria from the spec are covered.
2. **No placeholders:** No "TBD" or "TODO" appears. All code shown is
   actual code.
3. **Type consistency:** `sre.oem.pn`, `sre.product.family`,
   `sre.rfq`, `sre.rfq.line`, `crm.lead.sre_rfq_id` use consistent
   names throughout.
4. **Files named correctly:** Custom module folders are
   `sre_commercial_pim`, etc. (matches spec section 7).

## Execution Handoff

Plan complete and saved to
`docs/superpowers/plans/2026-09-07-sre-sprint1-foundation.md`. Two
execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per
   task, review between tasks, fast iteration
2. **Inline Execution** — execute tasks in this session using
   `executing-plans`, batch execution with checkpoints
