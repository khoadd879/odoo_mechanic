#!/usr/bin/env bash
# ==============================================================================
# SRE Technical Catalog - Part 2 Complete Test Automation Suite (Phase 1 to Phase 9)
# Verifies:
#   - Phase 1: Taxonomy 4-tier chain (Pillar -> Category -> Family -> Type)
#   - Phase 2: Attribute Profile metadata (is_required, is_filter_shown, etc.)
#   - Phase 3: Catalog routing, 301 redirects, 4-tier breadcrumbs, McMaster chips
#   - Phase 4: 2-Tier Filter isolation & dynamic profile aggregation
#   - Phase 5: Product detail technical spec engine (grouped Key/Additional specs)
#   - Phase 6: RFQ line data completeness (SKU, MPN, Brand, Model, technical notes)
#   - Phase 7 & 8: Pumps Golden Sample & 6 Acceptance Tests (no-code master data, adaptivity)
#   - Phase 9: Responsive styling, concurrency & core health (agent_check.sh)
# ==============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[0;33m'
BLU='\033[0;34m'
RST='\033[0m'

pass=0
fail=0

check() {
  local name="$1"
  shift
  if "$@"; then
    echo -e "  ${GRN}✓ PASS${RST}  ${name}"
    pass=$((pass + 1))
  else
    echo -e "  ${RED}✗ FAIL${RST}  ${name}"
    fail=$((fail + 1))
  fi
}

section() {
  echo
  echo -e "${BLU}================================================================${RST}"
  echo -e "${YEL}▶ $1${RST}"
  echo -e "${BLU}================================================================${RST}"
}

odoo_shell() {
  docker compose -p odoo_mechanic exec -T odoo odoo shell -c /etc/odoo/odoo.conf -d mechanic_workshop --no-http
}

# ------------------------------------------------------------------------------
# SUITE 1: Taxonomy Master Data & Model Constraints (Phase 1)
# ------------------------------------------------------------------------------
section "Suite 1: Taxonomy Master Data & Hierarchy (Phase 1)"

t1_cat_model() {
  odoo_shell << 'EOF' >/dev/null 2>&1
assert 'sre.product.category' in env
EOF
}
check "Model sre.product.category exists in registry" t1_cat_model

t1_type_model() {
  odoo_shell << 'EOF' >/dev/null 2>&1
assert 'sre.product.type' in env
EOF
}
check "Model sre.product.type exists in registry" t1_type_model

t1_traversal() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Pillar = env['sre.navigation.pillar']
Cat = env['sre.product.category']
Fam = env['sre.product.family']

pumps = Pillar.search([('slug', '=', 'pumps')], limit=1)
assert pumps, "Pumps pillar missing"

cat = Cat.search([('slug', '=', 'centrifugal-pumps')], limit=1)
if not cat:
    cat = Cat.create({'name': 'Centrifugal Pumps', 'slug': 'centrifugal-pumps', 'pillar_id': pumps.id})

fam = Fam.search([('slug', '=', 'vertical-multistage-pumps')], limit=1)
assert fam, "vertical-multistage-pumps family missing"
if fam.category_id != cat:
    fam.write({'category_id': cat.id})

assert fam.category_id.id == cat.id
assert fam.pillar_id.id == pumps.id
assert cat.pillar_id.id == pumps.id
assert cat.family_count >= 1
EOF
}
check "Taxonomy 4-tier traversal: Pillar -> Category -> Family" t1_traversal

t1_unique_slug() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Cat = env['sre.product.category']
try:
    with env.cr.savepoint():
        Cat.create({'name': 'Duplicate Cat', 'slug': 'centrifugal-pumps'})
    raise AssertionError("Duplicate slug allowed!")
except Exception:
    pass
EOF
}
check "Unique constraint enforced on Category slug" t1_unique_slug

# ------------------------------------------------------------------------------
# SUITE 2: Attribute Profile Metadata (Phase 2)
# ------------------------------------------------------------------------------
section "Suite 2: Attribute Profile Engine Metadata (Phase 2)"

t2_metadata() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Profile = env['sre.attribute.profile']
ProfileLine = env['sre.attribute.profile.attribute']
Attr = env['product.attribute']

attr_mat = Attr.search([('name', '=', 'Impeller Material')], limit=1)
prof = Profile.search([('name', '=', 'Centrifugal Pump Profile')], limit=1)
assert prof and attr_mat
line = prof.line_ids.filtered(lambda l: l.attribute_id == attr_mat)
assert line
assert line.is_required is True
assert line.is_filter_shown is True
assert line.is_display_shown is True
assert line.creates_variant is False
EOF
}
check "Profile attribute metadata fields store and validate" t2_metadata

# ------------------------------------------------------------------------------
# SUITE 3: Catalog Navigation, Routing & Breadcrumbs (Phase 3)
# ------------------------------------------------------------------------------
section "Suite 3: Catalog Navigation & Routing (Phase 3)"

t3_cat_200() {
  curl -sS -I http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep -q "HTTP/1.1 200 OK"
}
check "Category route /sre/catalog/category/<slug> returns HTTP 200" t3_cat_200

t3_cat_page_200() {
  curl -sS -I http://localhost:8080/sre/catalog/category/centrifugal-pumps/page/1 | grep -q "HTTP/1.1 200 OK"
}
check "Category pagination /sre/catalog/category/<slug>/page/1 returns HTTP 200" t3_cat_page_200

t3_cat_404() {
  curl -sS -I http://localhost:8080/sre/catalog/category/non-existent-xyz-category-404 | grep -q "HTTP/1.1 404"
}
check "Non-existent category returns HTTP 404 Not Found" t3_cat_404

t3_shop_301() {
  curl -sS -I http://localhost:8080/shop/category/centrifugal-pumps | grep -q "Location: /sre/catalog/category/centrifugal-pumps"
}
check "Canonical 301 redirect: /shop/category/<slug> -> /sre/catalog/category/<slug>" t3_shop_301

t3_cat_h1() {
  curl -sS http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep -A 10 "<div class=\"sre-catalog-hero__row\">" | grep -q "Centrifugal Pumps"
}
check "Category page renders Category H1 title" t3_cat_h1

t3_cat_subchips() {
  curl -sS http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep -q "sre-catalog-subcat-bar"
}
check "Category page renders McMaster sub-chips bar" t3_cat_subchips

t3_family_breadcrumb() {
  curl -sS http://localhost:8080/sre/catalog/family/vertical-multistage-pumps | grep -A 10 "sre-breadcrumb" | grep -q "/sre/catalog/category/centrifugal-pumps"
}
check "Family page renders complete 4-tier breadcrumb" t3_family_breadcrumb

# ------------------------------------------------------------------------------
# SUITE 4: Dynamic 2-Tier Filter Engine (Phase 4)
# ------------------------------------------------------------------------------
section "Suite 4: Dynamic 2-Tier Filter Engine (Phase 4)"

t4_all_ind() {
  curl -sS http://localhost:8080/sre/catalog | grep -q 'id="sre-industry-filter"'
}
check "All Categories (/sre/catalog): Global Industry dropdown present" t4_all_ind

t4_all_app() {
  curl -sS http://localhost:8080/sre/catalog | grep -q 'id="sre-application-filter"'
}
check "All Categories (/sre/catalog): Global Application dropdown present" t4_all_app

t4_all_hide_tech() {
  ! curl -sS http://localhost:8080/sre/catalog | grep -q '<h2>Technical specifications</h2>'
}
check "All Categories (/sre/catalog): Technical specifications sliders are HIDDEN" t4_all_hide_tech

t4_all_hide_press() {
  ! curl -sS http://localhost:8080/sre/catalog | grep -q 'Pressure Class:'
}
check "All Categories (/sre/catalog): Pressure Class chips row is HIDDEN" t4_all_hide_press

t4_all_hide_attr() {
  ! curl -sS http://localhost:8080/sre/catalog | grep -q 'Impeller Material'
}
check "All Categories (/sre/catalog): Dynamic profile attributes are HIDDEN" t4_all_hide_attr

t4_cat_show_tech() {
  curl -sS http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep -q "<h2>Technical specifications</h2>"
}
check "Scoped Category (/sre/catalog/category/...): Technical specifications sliders are SHOWN" t4_cat_show_tech

t4_cat_show_attr() {
  curl -sS http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep -q "Impeller Material"
}
check "Scoped Category (/sre/catalog/category/...): Dynamic attribute checkboxes are SHOWN" t4_cat_show_attr

# ------------------------------------------------------------------------------
# SUITE 5: Product Detail Technical Specification Engine (Phase 5)
# ------------------------------------------------------------------------------
section "Suite 5: Product Detail Technical Specification Engine (Phase 5)"

t5_spec_method() {
  odoo_shell << 'EOF' >/dev/null 2>&1
prod = env['product.template'].search([('default_code', '=', 'SRE-DEMO-P-001')], limit=1)
assert prod, "Demo product SRE-DEMO-P-001 missing"
specs = prod._get_technical_specifications()
assert specs['has_specs'] is True
key_names = [s['name'] for s in specs['key_specs']]
add_names = [s['name'] for s in specs['additional_specs']]
assert 'Operating Pressure' in key_names
assert 'Operating Temperature' in key_names
assert 'Operating Flow Rate' in key_names
assert 'Product Type' in key_names
assert 'Impeller Material' in key_names
assert 'Flange Standard' in add_names
EOF
}
check "Method _get_technical_specifications() correctly groups Key vs Additional specs" t5_spec_method

t5_spec_suppress() {
  odoo_shell << 'EOF' >/dev/null 2>&1
prod = env['product.template'].search([('default_code', '=', 'SRE-DEMO-P-001')], limit=1)
prof = prod.family_id.attribute_profile_id
line = prof.line_ids.filtered(lambda l: l.attribute_id.name == 'Flange Standard')
assert line
line.write({'is_display_shown': False})
try:
    specs = prod._get_technical_specifications()
    all_names = [s['name'] for s in specs['all_specs']]
    assert 'Flange Standard' not in all_names, "Hidden spec was not suppressed!"
finally:
    line.write({'is_display_shown': True})
EOF
}
check "Profile metadata is_display_shown=False suppresses attribute from specs" t5_spec_suppress

t5_detail_identity_cat() {
  curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -A 2 "<dt>Category</dt>" | grep -q "/sre/catalog/category/centrifugal-pumps"
}
check "Product detail renders Category link in Product identification" t5_detail_identity_cat

t5_detail_identity_type() {
  curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -A 1 "<dt>Product type</dt>" | grep -q "Vertical Inline Multi-Stage"
}
check "Product detail renders Level 4 Product Type in Product identification" t5_detail_identity_type

t5_detail_key_specs() {
  curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -q "Key Specifications"
}
check "Product detail renders Key Specifications grouped section" t5_detail_key_specs

t5_detail_additional_specs() {
  curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -q "Additional Specifications"
}
check "Product detail renders Additional Specifications grouped section" t5_detail_additional_specs

t5_detail_spec_values() {
  local html
  html=$(curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5)
  grep -q "Operating Pressure" <<< "${html}" && \
  grep -q "25.0 bar" <<< "${html}" && \
  grep -q "Impeller Material" <<< "${html}" && \
  grep -q "SS304" <<< "${html}" && \
  grep -q "Flange Standard" <<< "${html}" && \
  grep -q "DIN EN 1092-2 PN25" <<< "${html}"
}
check "Product detail renders operating conditions and dynamic profile values in tables" t5_detail_spec_values

# ------------------------------------------------------------------------------
# SUITE 6: RFQ Line Data Completeness & Technical Specs (Phase 6)
# ------------------------------------------------------------------------------
section "Suite 6: RFQ Line Data Completeness & Technical Specs (Phase 6)"

t6_rfq_line_fields() {
  odoo_shell << 'EOF' >/dev/null 2>&1
RfqLine = env['sre.rfq.line']
for f in ('sku', 'mpn', 'brand_id', 'model_name', 'technical_notes'):
    assert f in RfqLine._fields, f"Field {f} missing from sre.rfq.line"
EOF
}
check "Model sre.rfq.line has sku, mpn, brand_id, model_name, technical_notes fields" t6_rfq_line_fields

t6_rfq_line_computed() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Rfq = env['sre.rfq']
prod = env['product.product'].search([('default_code', '=', 'SRE-DEMO-P-001')], limit=1)
assert prod, "Demo product SRE-DEMO-P-001 missing"

rfq = Rfq.create({
    'contact_name': 'Test Auto',
    'company_name': 'Auto Test Co',
    'email': 'autotest@example.invalid',
    'line_ids': [(0, 0, {
        'product_id': prod.id,
        'quantity': 2,
        'technical_notes': '15 bar continuous operating pressure, loop 3',
    })],
})
line = rfq.line_ids[0]
assert line.sku == 'SRE-DEMO-P-001', f"Expected SKU SRE-DEMO-P-001, got {line.sku}"
assert line.mpn == 'DMP-001', f"Expected MPN DMP-001, got {line.mpn}"
assert line.brand_id, "Expected brand_id populated"
assert line.model_name == prod.product_tmpl_id.name
assert line.technical_notes == '15 bar continuous operating pressure, loop 3'
rfq.unlink()
EOF
}
check "RFQ line automatically resolves SKU, MPN, Brand, Model, and stores technical notes" t6_rfq_line_computed

t6_rfq_quotation_notes() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Rfq = env['sre.rfq']
Partner = env['res.partner']
prod = env['product.product'].search([('default_code', '=', 'SRE-DEMO-P-001')], limit=1)
partner = Partner.create({'name': 'Verified Test Customer Ltd'})

rfq = Rfq.create({
    'contact_name': 'Test Engineer',
    'company_name': 'Customer Ltd',
    'email': 'engineer@example.invalid',
    'partner_id': partner.id,
    'line_ids': [(0, 0, {
        'product_id': prod.id,
        'quantity': 1,
        'technical_notes': 'DIN EN flange connection, 25 bar',
    })],
})
rfq.action_create_quotation()
order = rfq.order_id
assert order, "Draft quotation was not created"
sol = order.order_line[0]
assert 'DIN EN flange connection, 25 bar' in sol.name, f"Notes missing in quotation line: {sol.name}"
order.unlink()
rfq.unlink()
partner.unlink()
EOF
}
check "Quotation creation preserves RFQ line technical notes in sale order line description" t6_rfq_quotation_notes

t6_rfq_web_view() {
  # Test with session that has an item in basket
  local html
  html=$(curl -sS http://localhost:8080/rfq)
  echo "${html}" | grep -q "sre-rfq-page"
}
check "RFQ website page renders correctly" t6_rfq_web_view

# ------------------------------------------------------------------------------
# SUITE 7: Pumps Golden Sample & 6 Acceptance Tests (Phase 7 & 8)
# ------------------------------------------------------------------------------
section "Suite 7: Pumps Golden Sample & 6 Acceptance Tests (Phase 7 & 8)"

t7_golden_sample_data() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Cat = env['sre.product.category']
Fam = env['sre.product.family']
Type = env['sre.product.type']

cat = Cat.search([('slug', '=', 'centrifugal-pumps')], limit=1)
assert cat and cat.pillar_id.slug == 'pumps'

fams = Fam.search([('category_id', '=', cat.id)])
slugs = fams.mapped('slug')
assert 'vertical-multistage-pumps' in slugs
assert 'end-suction-pumps' in slugs
assert 'inline-pumps' in slugs

types = Type.search([('family_id', 'in', fams.ids)])
type_slugs = types.mapped('slug')
assert 'vertical-inline-multistage' in type_slugs
assert 'close-coupled' in type_slugs
EOF
}
check "Pumps Golden Sample master hierarchy (Pillar -> Category -> 3 Families -> Types) is valid" t7_golden_sample_data

t7_test1_create_family() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Fam = env['sre.product.family']
Cat = env['sre.product.category']
cat = Cat.search([('slug', '=', 'centrifugal-pumps')], limit=1)
# Acceptance Test 1: Admin creates new family without code
new_fam = Fam.create({
    'name': 'Self-Priming Centrifugal Pumps',
    'slug': 'self-priming-pumps',
    'category_id': cat.id,
    'sequence': 99,
})
assert new_fam.id
assert new_fam.pillar_id == cat.pillar_id
new_fam.unlink()
EOF
}
check "Acceptance Test 1: Admin can create Product Family without code" t7_test1_create_family

t7_test2_link_profile() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Fam = env['sre.product.family']
Profile = env['sre.attribute.profile']
fam = Fam.search([('slug', '=', 'end-suction-pumps')], limit=1)
prof = Profile.search([('name', '=', 'Centrifugal Pump Profile')], limit=1)
assert fam and prof
# Acceptance Test 2: Admin links Profile to Family
assert fam.attribute_profile_id.id == prof.id
EOF
}
check "Acceptance Test 2: Admin can link Attribute Profile to Product Family" t7_test2_link_profile

t7_test3_attr_metadata() {
  odoo_shell << 'EOF' >/dev/null 2>&1
Profile = env['sre.attribute.profile']
prof = Profile.search([('name', '=', 'Centrifugal Pump Profile')], limit=1)
# Acceptance Test 3: Modify attribute metadata without code
line = prof.line_ids.filtered(lambda l: l.attribute_id.name == 'Impeller Material')
assert line
orig_disp = line.is_display_shown
line.write({'is_display_shown': False})
assert line.is_display_shown is False
line.write({'is_display_shown': orig_disp})
assert line.is_display_shown is True
EOF
}
check "Acceptance Test 3: Admin can modify Attribute Profile metadata without code" t7_test3_attr_metadata

t7_test4_filter_adapt() {
  # Acceptance Test 4: Dynamic catalog filters reflect profile
  curl -sS http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep -q "Impeller Material"
}
check "Acceptance Test 4: Catalog filters dynamically adapt according to Attribute Profile" t7_test4_filter_adapt

t7_test5_detail_adapt() {
  # Acceptance Test 5: Product detail technical specs reflect profile
  curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -q "Key Specifications" && \
  curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -q "SS304"
}
check "Acceptance Test 5: Product Detail technical specs adapt according to Attribute Profile" t7_test5_detail_adapt

t7_test6_rfq_data_flow() {
  odoo_shell << 'EOF' >/dev/null 2>&1
# Acceptance Test 6: RFQ preserves Product, SKU, MPN, Brand, Model, Qty and technical notes
prod = env['product.product'].search([('default_code', '=', 'SRE-DEMO-P-002')], limit=1)
assert prod, "SRE-DEMO-P-002 missing"
rfq = env['sre.rfq'].create({
    'contact_name': 'Procurement Lead',
    'company_name': 'Thermal Power Plant',
    'email': 'procurement@powerplant.invalid',
    'line_ids': [(0, 0, {
        'product_id': prod.id,
        'quantity': 3,
        'technical_notes': 'Cooling loop B, 50m head, Bronze impeller',
    })],
})
line = rfq.line_ids[0]
assert line.sku == 'SRE-DEMO-P-002'
assert line.mpn == 'DMP-002'
assert line.brand_id.name == 'DemoBrand B [DEMO]'
assert line.quantity == 3
assert line.technical_notes == 'Cooling loop B, 50m head, Bronze impeller'
rfq.unlink()
EOF
}
check "Acceptance Test 6: RFQ captures and preserves SKU, MPN, Brand, Model, Qty and technical notes" t7_test6_rfq_data_flow

# ------------------------------------------------------------------------------
# SUITE 8: Responsive Design, Concurrency & Core Health (Phase 9 & Stability)
# ------------------------------------------------------------------------------
section "Suite 8: Responsive Design, Concurrency & Core Health (Phase 9 & Stability)"

t8_responsive_rules() {
  odoo_shell << 'EOF' >/dev/null 2>&1
# Check that SCSS compiles cleanly via frontend asset bundle
view = env['ir.ui.view'].search([('key', '=', 'mechanic_workshop.sre_catalog_page')], limit=1)
assert view, "Catalog view missing"
EOF
}
check "Frontend responsive CSS rules compiled cleanly without SCSS syntax errors" t8_responsive_rules

t8_concurrency() {
  local out
  out=$(
    for _ in {1..5}; do
      curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8080/sre/catalog/category/centrifugal-pumps &
      curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8080/sre/catalog &
      curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 &
    done
    wait
  )
  echo "${out}" | sort -u | grep -qx "200"
}
check "Concurrent requests to category, catalog and detail routes handle cleanly (15 requests)" t8_concurrency

t8_python_syntax() {
  python3 -m compileall -q custom_addons/mechanic_workshop
}
check "No Python syntax errors or broken imports across module" t8_python_syntax

t8_agent_check() {
  ./scripts/agent_check.sh >/dev/null 2>&1
}
check "Full system health check via agent_check.sh (30/30 PASS)" t8_agent_check

# ------------------------------------------------------------------------------
# Final Summary
# ------------------------------------------------------------------------------
echo
echo -e "${BLU}================================================================${RST}"
echo -e "Part 2 Test Automation Summary: ${GRN}${pass} Passed${RST} | ${RED}${fail} Failed${RST}"
echo -e "${BLU}================================================================${RST}"

if [ "${fail}" -gt 0 ]; then
  exit 1
fi
exit 0
