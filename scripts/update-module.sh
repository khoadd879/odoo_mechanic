#!/usr/bin/env bash
# update-module.sh — install or upgrade a custom module in the running
# odoo_mechanic stack.
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

ADDONS_PATH="/usr/lib/python3/dist-packages/odoo/addons,/mnt/custom_addons,/mnt/oca_addons/brand,/mnt/oca_addons/product-attribute"
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
