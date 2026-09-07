# Verification

Skeleton bootstrap verification checklist:

- [ ] `docker compose -p odoo_mechanic config` exits 0
- [ ] `docker compose -p odoo_mechanic up -d` brings up `db` and
      `odoo` services
- [ ] `http://localhost:8080/web/login` returns HTTP 200
- [ ] `./scripts/update-module.sh mechanic_workshop --install`
      installs without tracebacks
- [ ] `./scripts/agent_check.sh` exits 0

Add feature-specific verification entries here as each feature is
shipped.
