# Mechanic Workshop

Mechanic Workshop is an Odoo 19 project scaffold for a mechanical
workshop business. The custom module starts empty and will grow
feature by feature as documented in `docs/FEATURE_LIST.json`.

The stack is isolated from `/home/khoa/Company/odoo` (legacy) and
`/home/khoa/Company/odoo_testing` (fashion eCommerce).

## Quick start

```bash
docker compose -p odoo_mechanic up -d db
./scripts/update-module.sh mechanic_workshop --install
docker compose -p odoo_mechanic up -d odoo
./scripts/agent_check.sh
```

Open <http://localhost:8080>.

## Layout

- `docker-compose.yml` — isolated Odoo 19/PostgreSQL stack
- `odoo.conf` — local database and server configuration
- `custom_addons/mechanic_workshop/` — empty starter module
- `docs/` — scope, architecture, feature status, and verification
- `scripts/` — module update and project health checks

The project must never mount or modify `/home/khoa/Company/odoo` or
`/home/khoa/Company/odoo_testing`.
