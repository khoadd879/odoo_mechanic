#!/usr/bin/env bash
# update-module.sh — install or upgrade a custom module in the running
# odoo_mechanic stack.
#
# After every upgrade (or install) we flush the compiled frontend bundle
# and generated sitemap caches from ``ir.attachment``, then restart the
# Odoo container. This makes new SCSS/JS and public routes visible on the
# next request instead of waiting for cache expiry.
#
# Usage:
#   ./scripts/update-module.sh [module_name] [--install]
#
# Examples:
#   ./scripts/update-module.sh mechanic_workshop             # upgrade only
#   ./scripts/update-module.sh mechanic_workshop --install   # install on first run

set -eu

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

MODULE="${1:-mechanic_workshop}"
INSTALL_FLAG="${2:-}"

ADDONS_PATH="/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons,/mnt/oca_addons/brand,/mnt/oca_addons/product-attribute,/mnt/oca_addons/rest-framework,/mnt/oca_addons/web-api"
DATABASE="mechanic_workshop"

if [ "${INSTALL_FLAG}" = "--install" ]; then
  echo ">> Installing module '${MODULE}' into '${DATABASE}'"
  docker compose -p odoo_mechanic run --rm odoo \
      odoo -d "${DATABASE}" \
         --config=/etc/odoo/odoo.conf \
         --addons-path="${ADDONS_PATH}" \
         -i "${MODULE}" \
         --stop-after-init \
         --no-http
else
  echo ">> Updating module '${MODULE}' in the running stack"
  docker compose -p odoo_mechanic exec -T odoo \
      odoo -d "${DATABASE}" \
         --config=/etc/odoo/odoo.conf \
         --addons-path="${ADDONS_PATH}" \
         -u "${MODULE}" \
         --stop-after-init \
         --no-http
fi

# ---------------------------------------------------------------------------
# Invalidate generated frontend and sitemap attachments so new assets and
# public routes are rebuilt for visitors after this module update.
# ---------------------------------------------------------------------------
echo ">> Invalidating frontend asset and sitemap caches"
docker compose -p odoo_mechanic exec -T odoo \
    odoo shell -d "${DATABASE}" --no-http <<'PY' >/dev/null
attachments = env['ir.attachment'].sudo().search([
    ('name', '=like', 'web.assets_frontend%.min.%'),
    '|', ('res_model', '=', 'ir.ui.view'),
         ('res_model', '=', False),
])
if attachments:
    names = ', '.join(attachments.mapped('name'))
    print('   unlinking %d asset attachment(s): %s' % (len(attachments), names))
    attachments.unlink()
sitemaps = env['ir.attachment'].sudo().search([
    ('url', '=like', '/sitemap-%'),
])
if sitemaps:
    print('   unlinking %d generated sitemap cache(s)' % len(sitemaps))
    sitemaps.unlink()
# ``odoo shell`` rolls its transaction back on process exit unless the
# standalone maintenance command commits explicitly.
env.cr.commit()
PY

echo ">> Restarting Odoo to rebuild the asset bundles"
docker compose -p odoo_mechanic restart odoo >/dev/null

echo ">> Waiting for the public website to become ready"
READY=0
for ATTEMPT in $(seq 1 60); do
  if curl -fsS -o /dev/null --max-time 5 http://localhost:8080/; then
    READY=1
    break
  fi
  sleep 1
done
if [ "${READY}" -ne 1 ]; then
  echo ">> Odoo did not become ready within 60 seconds" >&2
  docker compose -p odoo_mechanic ps >&2
  exit 1
fi
echo ">> Odoo website is ready"
