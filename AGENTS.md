# AGENTS.md — Mechanic Workshop

Binding instructions for coding agents working in this repository.
The repo is the source of truth; read the active feature docs before
changing code and update them whenever scope changes.

## 1. Project identity

| Field | Value |
|---|---|
| Project | Mechanic Workshop |
| Odoo version | 19.0 |
| Docker project | `odoo_mechanic` |
| Database | `mechanic_workshop` |
| Host URL | http://localhost:8080 |
| Odoo ports | host `8080` → `8069`; host `8083` → `8072` |
| Custom addons | `./custom_addons` |
| Active module | `mechanic_workshop` |
| Repo root | `/home/khoa/Company/odoo_mechanic` |

Never touch the legacy project at `/home/khoa/Company/odoo`.
Never touch the fashion project at `/home/khoa/Company/odoo_testing`.
Never reuse their compose projects, networks, volumes, filestores, or
ports.

## 2. Architecture boundary

Native Odoo modules own products, variants, sales, purchases, stock,
invoicing, payments, and reporting. Custom code may extend those
modules but must not replace their core flows.

The `mechanic_workshop` module is the only project-owned addon. It
starts empty and grows feature by feature as documented in
`docs/FEATURE_LIST.json`.

## 3. Workflow rules

1. Read `docs/PROGRESS.md` and the active feature in
   `docs/FEATURE_LIST.json` before changing code.
2. Work on one independently verifiable feature at a time.
3. Prefer native Odoo 19 and compatible OCA modules over custom logic.
4. Never patch Odoo core.
5. Preserve unrelated user changes.
6. Verify real behavior before claiming completion.
7. Update `docs/PROGRESS.md` and `docs/FEATURE_LIST.json` with fresh
   evidence.
8. Before deleting project-owned Docker volumes, create and verify an
   offline backup. Only `odoo_mechanic_db` and `odoo_mechanic_data` are
   in scope.

## 4. Definition of done

A feature is done only when:

- code/config is committed in this repo;
- `docker compose -p odoo_mechanic up -d` succeeds;
- the relevant module install/update succeeds;
- no new traceback or critical log entry exists;
- every acceptance criterion has fresh evidence;
- `./scripts/agent_check.sh` exits 0;
- progress and feature-list docs are current.

## 5. Approved commands

```bash
docker compose -p odoo_mechanic up -d
docker compose -p odoo_mechanic stop
docker compose -p odoo_mechanic ps
docker compose -p odoo_mechanic logs --tail=200 odoo
./scripts/update-module.sh mechanic_workshop
./scripts/update-module.sh mechanic_workshop --install
./scripts/agent_check.sh
```

Do not run `docker compose down` against the legacy or fashion
projects. Do not delete broad directories or volumes. Use exact
project-owned targets.

## 6. When blocked

Capture the failing command and full relevant error. Record the
blocker in `docs/PROGRESS.md`, fix the smallest root cause first, and
do not mark the feature done while the blocker remains.
