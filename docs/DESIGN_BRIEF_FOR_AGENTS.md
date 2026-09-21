# SRE Commercial Website — Design Brief for Agents

> **Purpose**: This document gives any agent full context to understand, review, and modify the website design for the SRE Commercial project. Read this before making any design changes.

---

## 1. Project Overview

| Field | Value |
|---|---|
| Project | SRE Commercial — Digital Product Distribution Platform |
| Platform | Odoo 19 Website (custom module `mechanic_workshop`) |
| Business Type | B2B Industrial Technical Commerce |
| Target Scale | 100s → 10,000–100,000+ SKUs |
| MagicPath Project ID | `450808259931176960` |
| MagicPath Project Name | SRE Commercial Platform |
| MagicPath Component ID | `450808299164688384` |
| MagicPath Component Name | `rapid-lake-8483` |
| Active Revision ID | `450819903923060736` (McMaster Visual Asset System) |
| MagicPath Owner | Trần Khoa (`khoadd879@gmail.com`) |
| Canvas URL | https://www.magicpath.ai/files/450808259931176960 |
| Component URL | https://api.magicpath.ai/v1/rapid-lake-8483 |

---

## 2. Business Domain

SRE Commercial is a **B2B industrial product distributor** specializing in:

1. **Industrial HVAC** — AHU components, motoric actuators, PICV, DDC controllers
2. **Boiler & Thermal Systems** — Electrode probes, blowdown valves, flame scanners, burner parts
3. **Pumps & Fluid Handling** — Vertical multistage CR, end-suction, cartridge seals
4. **Valves** — Control valves, steam traps, isolation, safety relief valves
5. **Heat Exchangers** — PHE, gasketed plate packs, BPHE
6. **Instrumentation** — Pressure transmitters (4-20mA), flowmeters, DP gauges
7. **Controls & Automation** — DDC controllers, BACnet, VFD
8. **Industrial Spare Parts** — Gaskets (PN16-PN40), packing overhaul kits, OEM spares

**Key Brands**: Grundfos, Danfoss, Gestra (Spirax Sarco), Siemens, Belimo, Honeywell, Alfa Laval, WIKA, Endress+Hauser

---

## 3. Core User Flow (NOT E-Commerce)

> ⚠️ **Critical**: This is NOT a fashion/retail e-commerce site. Do NOT use Add-to-Cart flows.

The architecture follows the **industrial procurement paradigm**:

```
Search → Technical Discovery → Product Qualification → RFQ → Sales → Procurement → Delivery → Repeat Order
```

### Three Customer Personas

| Persona | Description | Expected UX |
|---|---|---|
| **A. Knows exactly** | Has OEM Part No., MPN, Model, SKU | Fast search → instant result |
| **B. Knows category** | Needs "boiler probe" or "steam trap" | Browse categories → parametric filters |
| **C. Knows problem** | Has "boiler water level issue" | Application/Problem/Industry navigation |

---

## 4. Design Philosophy — McMaster-Carr Inspired

The design MUST follow the **McMaster-Carr** industrial commerce style. This is the #1 reference:

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--sre-green-deep` | `#004b2b` | Header masthead, primary brand |
| `--sre-green-dark` | `#00351e` | Header hover/active states |
| `--sre-green-medium` | `#006838` | Links, part numbers |
| `--sre-gold` | `#f59e0b` | CTA buttons (FIND, Submit RFQ) |
| `--sre-gold-hover` | `#d97706` | CTA hover state |
| `--sre-bg-white` | `#ffffff` | Main content background |
| `--sre-bg-warm` | `#fafaf8` | Alternating table rows, section bg |
| `--sre-border` | `#e2e2e0` | Table borders, dividers |
| `--sre-text-primary` | `#1a1a1a` | Body text |
| `--sre-text-secondary` | `#666666` | Secondary/spec text |
| `--sre-badge-blue` | `#2563eb` | CAD badge, technical tags |
| `--sre-badge-red` | `#dc2626` | Stock alerts, warnings |

### Typography

- **Font Family**: `Inter`, `system-ui`, `-apple-system`, sans-serif
- **Header/Brand**: Bold, technical, uppercase where appropriate
- **Body**: Clean, high readability, dense data display
- **Spec Tables**: Monospace-like alignment for part numbers and technical values

### Design Principles

1. **White background, maximum contrast** — Engineers need to read specs without eye fatigue
2. **No dark mode / gaming / crypto aesthetic** — Professional, utilitarian, trustworthy
3. **Information density over decoration** — More data per pixel, less whitespace waste
4. **Multi-column product directory** — Categories visible at a glance on homepage
5. **Parametric spec tables** — Part numbers, specs, CAD download, quantity, RFQ all on one row
6. **Zero decorative gradients** — Flat, clean borders with subtle shadows only
7. **Green masthead + gold CTA** — McMaster-Carr signature pattern

---

## 5. Page Structure & Components

### 5.1 Header (`SREHeader`)
- Deep forest green masthead (`#004b2b`)
- Logo: "SRE Commercial" in bold technical font
- **Prominent search bar** with gold **`FIND`** button (search is P0 priority)
- Service bar: *"98% of in-stock items ship today • Same or Next Day Delivery"*
- Quick access buttons: **Boiler Part Finder**, **Fast Order Pad**, **RFQ Basket** (with item count)
- Navigation: HVAC & Building | Boiler & Thermal | Pumps | Valves | Heat Exchangers | Instrumentation | Controls & Automation | Industrial Spare Parts

### 5.2 Homepage / Department Index (`SREHero`)
- **NO** hero banners or marketing carousels
- **6-column product department index** — McMaster-Carr style multi-column directory
  1. Valves & Steam Handling
  2. Boiler & Thermal Systems
  3. Pumps & Fluid Handling
  4. HVAC & Building Controls
  5. Instrumentation & Gauges
  6. Maintenance Hardware & Kits
- Each subcategory shows SKU count and links directly to parametric tables
- Optional: "New Products", "Popular Parts" sidebars (minimal, data-driven)

### 5.3 Product Catalog (`SREProductCatalog`)
- **Left sidebar**: Category tree + parametric filters (brand, pressure rating, size, connection type, etc.)
- **Main content**: High-density data table with columns:
  - Part Number (green, clickable)
  - Product Name / Description
  - Brand
  - Key Specs (2-3 most important per category)
  - `[CAD]` badge link
  - Stock status indicator
  - Qty input + **Add to RFQ** button
- **Sorting**: By part number, price, brand, relevance
- **Pagination**: Results per page selector (25/50/100)

### 5.4 Product Detail (`SREProductDetail`)
- **Header**: Part number (large, bold), brand, product family
- **Image gallery**: Product photos, technical drawings, dimensional diagrams
- **Specifications table**: Full parametric data in 2-column key-value format
- **Documents section**: Datasheets (PDF), CAD files (DWG/STEP/STP), installation manuals
- **Cross-reference table**: Compatible alternatives, replacement parts
- **RFQ action**: Quantity input + "Add to RFQ" + "Request Pricing" buttons
- **Related products**: Same family, compatible accessories

### 5.5 Boiler Part Finder (`BoilerPartFinder`)
- Specialized wizard for boiler parts identification
- Step 1: Select boiler brand/model
- Step 2: Select system (water level, combustion, safety, etc.)
- Step 3: Browse matching parts with specs
- Results shown in parametric table format

### 5.6 Fast Order Pad (`FastOrderPad`)
- McMaster-Carr style quick-order interface
- Multi-line input: Part Number | Quantity | Notes per line
- Paste from Excel/CSV/BOM support
- Instant part number validation and preview
- One-click "Submit as RFQ"

### 5.7 RFQ Drawer (`SRERFQDrawer`)
- Slide-out panel (right side) showing current RFQ basket
- Line items: Part No., Name, Qty, Notes, Remove
- Customer info: Company, Contact, Email, Phone
- Project/PO reference field
- "Submit RFQ" and "Save Draft" actions
- Email confirmation flow

### 5.8 Footer (`SREFooter`)
- Company info: SRE Commercial
- Contact details, office hours
- Quick links: Categories, Technical Library, About, Contact
- Certifications/partnerships logos
- Minimal, professional

---

## 6. MagicPath Design Workflow

### Viewing the Current Design
```bash
# Open project canvas in browser
npx -y magicpath-ai view 450808259931176960

# List components
npx -y magicpath-ai list-components 450808259931176960 -o json

# Inspect specific component
npx -y magicpath-ai inspect rapid-lake-8483 -o json
```

### Updating the Design
```bash
# Step 1: Start code session
npx -y magicpath-ai code start \
  --project 450808259931176960 \
  --dir /path/to/output/dir

# Step 2: Write/update React+TSX component files in the output dir
# Each component is a self-contained .tsx file with inline styles

# Step 3: Submit updated code
npx -y magicpath-ai code submit \
  --dir /path/to/output/dir \
  --wait -o json
```

### Component Source Files Location
All generated design components are stored at:
```
<artifact_dir>/scratch/sre_canvas/src/components/generated/
```

Files:
- `sreData.ts` — Product data, types, sample data
- `SREHeader.tsx` — Header/masthead component
- `SREHero.tsx` — Homepage department index
- `SREProductCatalog.tsx` — Product listing with filters
- `SREProductDetail.tsx` — Individual product detail page
- `BoilerPartFinder.tsx` — Boiler part identification wizard
- `FastOrderPad.tsx` — Quick order pad
- `SRERFQDrawer.tsx` — RFQ basket drawer
- `SREFooter.tsx` — Footer component
- `SRECommercialPlatform.tsx` — Main app shell (composes all components)

### Tech Stack for Design Components
- **React** + **TypeScript** (TSX)
- **Inline CSS-in-JS** (no external CSS framework)
- Components must be self-contained for MagicPath canvas rendering
- Use `React.CSSProperties` for all styles
- No external dependencies beyond React

---

## 7. Key Design References

### Primary Reference
- **McMaster-Carr** (https://www.mcmaster.com/) — The gold standard for industrial B2B commerce UX. Study their:
  - Multi-column homepage category directory
  - Search-first architecture
  - Dense parametric tables
  - Clean white + green color scheme
  - Fast order flow

### Supplementary References
- **Grainger** (https://www.grainger.com/) — Industrial MRO distributor
- **MSC Industrial** (https://www.mscdirect.com/) — Tooling & metalworking
- **RS Components** (https://www.rs-online.com/) — Electronic & industrial components

---

## 8. Source Documents

| Document | Location | Purpose |
|---|---|---|
| SRE Transformation Brief V2 | `docs/SRE Commercial Website Transformation Brief.docx.md` | Full requirements specification |
| PIM Master V2 Governance | `docs/SRE_COMMERCIAL_WEBSITE_PIM_MASTER_v2.xlsx - README_GOVERNANCE.csv` | Product data governance rules |
| Project Brief | `docs/PROJECT_BRIEF.md` | Odoo project setup overview |
| Feature List | `docs/FEATURE_LIST.json` | Feature tracking |
| Progress Log | `docs/PROGRESS.md` | Implementation progress |

---

## 9. DO NOTs

- ❌ Do NOT use dark mode / glassmorphism / neon colors
- ❌ Do NOT add hero banners, sliders, or marketing carousels
- ❌ Do NOT use "Add to Cart" — use "Add to RFQ" / "Request Quote"
- ❌ Do NOT show prices (this is RFQ-based pricing)
- ❌ Do NOT make it look like a fashion/retail e-commerce site
- ❌ Do NOT prioritize aesthetics over information density
- ❌ Do NOT use rounded cards with large padding — use dense, table-driven layouts
- ❌ Do NOT change product taxonomy, SKU logic, or brand logic without SRE approval

## 10. DOs

- ✅ Prioritize **search** above everything else
- ✅ Use **dense parametric tables** for product browsing
- ✅ Show **part numbers prominently** (green, bold)
- ✅ Include **CAD download** badges on product rows
- ✅ Support **paste-from-Excel** in Fast Order Pad
- ✅ Keep the **RFQ basket** always accessible
- ✅ Use **white backgrounds** with clean borders
- ✅ Make everything feel **fast, professional, utilitarian**
- ✅ Follow McMaster-Carr's layout philosophy
- ✅ Ensure all components work independently (composable architecture)
