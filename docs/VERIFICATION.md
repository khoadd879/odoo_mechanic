# Verification

Skeleton bootstrap verification checklist:

- [x] `docker compose -p odoo_mechanic config` exits 0
- [x] `docker compose -p odoo_mechanic up -d` brings up `db` and `odoo` services
- [x] `http://localhost:8080/web/login` returns HTTP 200
- [x] `./scripts/update-module.sh mechanic_workshop --install` installs without tracebacks
- [x] `./scripts/agent_check.sh` exits 0

Add feature-specific verification entries here as each feature is
shipped.
