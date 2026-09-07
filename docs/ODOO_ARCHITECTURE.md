# Odoo Architecture

## Target

- Odoo: 19.0 Community
- PostgreSQL: 15
- Database: `mechanic_workshop`
- Custom module: `mechanic_workshop`

## Native modules

The exact list of native modules the project will depend on is
decided feature by feature. Typical candidates for a mechanical
workshop:

| Module | Responsibility |
|---|---|
| `product`, `product_attribute` | product master, variants, attributes |
| `stock`, `purchase_stock` | inventory and replenishment |
| `sale`, `sale_management` | quotations and sales orders |
| `purchase` | vendors, RFQs, purchase orders |
| `account`, `account_payment` | invoicing and payments |
| `mrp`, `mrp_repair` | manufacturing and repair orders |
| `hr`, `fleet` | employees, attendance, vehicles |
| `website`, `website_sale` | public site and storefront (if needed) |
| `contacts` | customer and vendor directory |

## Custom module boundary

`custom_addons/mechanic_workshop` starts empty. As features are
approved they must:

- Extend native Odoo modules instead of replacing them.
- Add new models only when no native model fits.
- Follow OCA conventions: type hints (Python 3.12+), `SQL()` builder
  for raw SQL, OWL 3.x patterns, direct `invisible`/`readonly`
  expressions, `Command` class for x2many operations.
- Ship with `ir.model.access.csv` whenever a new model is added.
- Be verifiable end-to-end via `scripts/agent_check.sh`.

## Search decision

Before adding any new functionality, search Odoo 19 core, Odoo
Enterprise, and OCA 19 for an existing module or pattern. Extend
the closest match first; only build from scratch when nothing
appropriate exists.
