#!/usr/bin/env bash

# Project health and storefront acceptance checks for Mechanic Workshop.

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
  docker compose -p odoo_mechanic ps --services --status running 2>/dev/null |
    rg -qx "$1"
}

volume_exists() {
  docker volume ls --format '{{.Name}}' | rg -qx "$1"
}

no_foreign_mount() {
  ! docker compose -p odoo_mechanic config 2>/dev/null |
    rg -q "/home/khoa/Company/(odoo|odoo_testing)/"
}

http_contains() {
  local url="$1"
  local marker="$2"
  curl -fsS --max-time 15 "${url}" | rg -F "${marker}" >/dev/null
}

http_excludes() {
  local url="$1"
  local marker="$2"
  ! curl -fsS --max-time 15 "${url}" | rg -F "${marker}" >/dev/null
}

shop_redirects_to_catalog() {
  local response
  response="$(curl -sS -o /dev/null --max-time 15 \
    -w '%{http_code} %{redirect_url}' \
    'http://localhost:8080/shop?search=DMV-001')"
  [ "${response}" = "301 http://localhost:8080/sre/catalog?search=DMV-001" ]
}

suggestion_endpoint_works() {
  curl -fsS --max-time 15 \
    'http://localhost:8080/sre/search_suggest?term=DMV-001' |
    python3 -c 'import json, sys
data = json.load(sys.stdin)
assert data["term"] == "DMV-001"
assert any(item.get("mpn") == "DMV-001" for tier in data["tiers"] for item in tier["items"])'
}

product_detail_works() {
  local product_url
  product_url="$(curl -fsS --max-time 15 \
    'http://localhost:8080/sre/catalog?search=DMV-001' |
    rg -o 'href="/shop/[^"]+' | rg 'sre-demo-v-001' | head -n 1 |
    cut -d'"' -f2)"
  [ -n "${product_url}" ] &&
    http_contains "http://localhost:8080${product_url}" "Add to RFQ" &&
    http_contains "http://localhost:8080${product_url}" "Product identification"
}

rfq_session_flow_works() {
  local cookie_file product_page rfq_page product_url csrf_token product_id
  cookie_file="$(mktemp)"
  product_page="$(mktemp)"
  rfq_page="$(mktemp)"
  product_url="$(curl -fsS --max-time 15 \
    'http://localhost:8080/sre/catalog?search=DMV-001' |
    rg -o 'href="/shop/[^"]+' | rg 'sre-demo-v-001' | head -n 1 |
    cut -d'"' -f2)" || return 1
  curl -fsS --max-time 15 -c "${cookie_file}" -b "${cookie_file}" \
    "http://localhost:8080${product_url}" >"${product_page}" || return 1
  csrf_token="$(rg -o 'name="csrf_token" value="[^"]+' \
    "${product_page}" | head -n 1 | cut -d'"' -f4)"
  product_id="$(rg -o '<option value="[0-9]+"' "${product_page}" |
    head -n 1 | rg -o '[0-9]+')"
  curl -fsS -L --max-time 15 -c "${cookie_file}" -b "${cookie_file}" \
    http://localhost:8080/rfq/add \
    --data-urlencode "csrf_token=${csrf_token}" \
    --data-urlencode "product_id=${product_id}" \
    --data-urlencode 'quantity=2' >"${rfq_page}" || return 1
  rg -qF 'Demo Valve 001 [DEMO]' "${rfq_page}" || return 1
  rg -qF 'value="2.0"' "${rfq_page}" || return 1
  csrf_token="$(rg -o 'name="csrf_token" value="[^"]+' \
    "${rfq_page}" | head -n 1 | cut -d'"' -f4)"
  curl -fsS -L --max-time 15 -c "${cookie_file}" -b "${cookie_file}" \
    http://localhost:8080/rfq/update \
    --data-urlencode "csrf_token=${csrf_token}" \
    --data-urlencode "product_id=${product_id}" \
    --data-urlencode 'quantity=3.5' >"${rfq_page}" || return 1
  rg -qF 'value="3.5"' "${rfq_page}" || return 1
  curl -fsS -L --max-time 15 -c "${cookie_file}" -b "${cookie_file}" \
    http://localhost:8080/rfq/update \
    --data-urlencode "csrf_token=${csrf_token}" \
    --data-urlencode "product_id=${product_id}" \
    --data-urlencode 'remove=1' >"${rfq_page}" || return 1
  rg -qF 'Your RFQ list is empty' "${rfq_page}"
}

frontend_assets_compile() {
  local page_file asset_path asset_file
  page_file="$(mktemp)"
  asset_file="$(mktemp)"
  curl -fsS --max-time 15 http://localhost:8080/ >"${page_file}" || return 1
  asset_path="$(rg -o '/web/assets/[^"]+web.assets_frontend[^" ]+\.css' \
    "${page_file}" | head -n 1)"
  [ -n "${asset_path}" ] || return 1
  curl -fsS --max-time 30 "http://localhost:8080${asset_path}" >"${asset_file}" || return 1
  rg -qF '.sre-home-hero' "${asset_file}" &&
    ! rg -qF 'css_error_message' "${asset_file}"
}

privacy_invariants_hold() {
  docker compose -p odoo_mechanic exec -T odoo \
    odoo shell -d mechanic_workshop --no-http 2>/dev/null <<'PY' | rg -q '^SRE_PRIVACY_OK$'
brand_leaks = env['product.brand'].sudo().search_count([
    ('partner_id', '!=', False),
])
demo_costs = env['product.template'].sudo().search_count([
    ('default_code', '=like', 'SRE-DEMO-%'),
    ('standard_price', '!=', 0),
])
public_acl_ids = (
    'mechanic_workshop.access_sre_attr_profile_public',
    'mechanic_workshop.access_sre_attr_profile_line_public',
    'mechanic_workshop.access_sre_oem_pn_public',
)
acl_is_closed = all(
    acl and not any((acl.perm_read, acl.perm_write, acl.perm_create, acl.perm_unlink))
    for acl in (env.ref(xmlid, raise_if_not_found=False) for xmlid in public_acl_ids)
)
if not brand_leaks and not demo_costs and acl_is_closed:
    print('SRE_PRIVACY_OK')
PY
}

manifest_xml_is_valid() {
  python3 - <<'PY'
import ast
from pathlib import Path
from xml.etree import ElementTree

module = Path('custom_addons/mechanic_workshop')
manifest = ast.literal_eval((module / '__manifest__.py').read_text())
for relative_path in manifest.get('data', []):
    path = module / relative_path
    if path.suffix == '.xml':
        ElementTree.parse(path)
PY
}

section "Project files"
check "AGENTS.md" test -f AGENTS.md
check "module manifest" test -f custom_addons/mechanic_workshop/__manifest__.py
check "module __init__.py" test -f custom_addons/mechanic_workshop/__init__.py
check "docker-compose.yml" test -f docker-compose.yml
check "odoo.conf" test -f odoo.conf
check ".env.example" test -f .env.example
check "manifest XML parses" manifest_xml_is_valid
check "Python compiles" python3 -m compileall -q custom_addons/mechanic_workshop
check "shell scripts parse" bash -n scripts/agent_check.sh scripts/update-module.sh

section "Compose"
check "compose config valid" docker compose -p odoo_mechanic config
check "Odoo running" service_is_running odoo
check "PostgreSQL running" service_is_running db
check "database volume exists" volume_exists odoo_mechanic_db
check "filestore volume exists" volume_exists odoo_mechanic_data
check "no foreign project mount" no_foreign_mount

section "Connected storefront"
check "homepage renders professional hero" http_contains \
  http://localhost:8080/ "sre-home-hero"
check "homepage search targets catalog" http_contains \
  http://localhost:8080/ 'action="/sre/catalog"'
check "/shop search redirects canonically" shop_redirects_to_catalog
check "catalog exact MPN search works" http_contains \
  'http://localhost:8080/sre/catalog?search=DMV-001' "Demo Valve 001 [DEMO]"
check "catalog exact search returns one result" http_contains \
  'http://localhost:8080/sre/catalog?search=DMV-001' '<strong>1</strong>'
check "catalog empty state works" http_contains \
  'http://localhost:8080/sre/catalog?search=SRE-NO-SUCH-PART' "No matching product found"
check "catalog sort and table modes work" http_contains \
  'http://localhost:8080/sre/catalog?order=name_desc&layout_mode=table&per_page=24' "sre-products-table"
check "autocomplete returns matching MPN" suggestion_endpoint_works
check "product detail connects to RFQ" product_detail_works
check "RFQ page reachable" http_contains \
  http://localhost:8080/rfq "Your RFQ list is empty"
check "RFQ add, update and remove work" rfq_session_flow_works
check "retail price is absent from catalog" http_excludes \
  'http://localhost:8080/sre/catalog?search=DMV-001' "product_price"
check "frontend CSS bundle compiles" frontend_assets_compile
check "public privacy invariants" privacy_invariants_hold

section "Recent logs"
if docker compose -p odoo_mechanic logs --tail=200 odoo 2>/dev/null |
  rg "Traceback \(most recent call last\)|CRITICAL|mechanic_workshop.*ERROR" |
  rg -q .; then
  echo -e "${RED}FAIL${RST}  traceback/critical/module error found"
  fail=$((fail + 1))
else
  echo -e "${GRN}PASS${RST}  no traceback/critical/module error"
  pass=$((pass + 1))
fi

section "Repository"
git status --short || true

echo
echo -e "Passed: ${GRN}${pass}${RST}  Failed: ${RED}${fail}${RST}"
exit "${fail}"
