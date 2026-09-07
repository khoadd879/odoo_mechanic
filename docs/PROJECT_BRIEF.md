# Mechanic Workshop — Project Brief

## Goal

Bootstrap an isolated Odoo 19 stack for a mechanical workshop
business. The custom `mechanic_workshop` module starts empty and will
grow feature by feature as documented in `docs/FEATURE_LIST.json`.

## Success

- A clean, reproducible Odoo 19 + PostgreSQL 15 stack runs at
  `http://localhost:8080` entirely separate from `/Company/odoo`
  (legacy) and `/Company/odoo_testing` (fashion).
- The `mechanic_workshop` module installs successfully with no
  tracebacks or critical log entries.
- Native Odoo modules own every business flow (products, sales,
  purchases, stock, accounting); the custom module only fills
  project-specific gaps as each feature is approved.

## Current scope

- Odoo 19 Community, PostgreSQL 15
- Docker project `odoo_mechanic`, database `mechanic_workshop`,
  host ports `8080` (web) and `8083` (longpolling)
- Named volumes `odoo_mechanic_db` and `odoo_mechanic_data` (never
  reused by other projects)
- Empty starter addon at `custom_addons/mechanic_workshop/`

## Deferred

- All business features (catalog, repair orders, work orders, etc.)
  are tracked in `docs/FEATURE_LIST.json` and unlocked one at a time.
- Real payment-provider credentials.
- Production TLS, backups, monitoring, and proxy.
