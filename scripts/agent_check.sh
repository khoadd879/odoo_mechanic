#!/usr/bin/env bash

# agent_check.sh — minimal project health checks for the empty
# mechanic_workshop scaffold. Extend this file feature by feature as
# the project grows.

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
    grep -qx "$1"
}

volume_exists() {
  docker volume ls --format '{{.Name}}' | grep -qx "$1"
}

no_foreign_mount() {
  ! docker compose -p odoo_mechanic config 2>/dev/null |
    grep -Eq "/home/khoa/Company/(odoo|odoo_testing)/"
}

section "Project files"
check "AGENTS.md" test -f AGENTS.md
check "module manifest" test -f custom_addons/mechanic_workshop/__manifest__.py
check "module __init__.py" test -f custom_addons/mechanic_workshop/__init__.py
check "docker-compose.yml" test -f docker-compose.yml
check "odoo.conf" test -f odoo.conf
check ".env.example" test -f .env.example

section "Compose"
check "compose config valid" docker compose -p odoo_mechanic config
check "Odoo running" service_is_running odoo
check "PostgreSQL running" service_is_running db
check "database volume exists" volume_exists odoo_mechanic_db
check "filestore volume exists" volume_exists odoo_mechanic_data
check "no foreign project mount" no_foreign_mount

section "Recent logs"
if docker compose -p odoo_mechanic logs --tail=200 odoo 2>/dev/null |
  grep -E "Traceback \(most recent call last\)|CRITICAL|mechanic_workshop.*ERROR" |
  grep -q .; then
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
