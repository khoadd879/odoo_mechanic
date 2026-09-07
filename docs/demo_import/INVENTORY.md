# Inventory — Dữ liệu DEMO đã chuẩn bị

> **Trạng thái hiện tại: CSV đã chuẩn bị, CHƯA import vào Odoo.**
> File này liệt kê chính xác 13 bản ghi sẽ được tạo khi import đủ 4
> file CSV trong thư mục này. Dùng để dọn dẹp an toàn sau khi kiểm thử,
> **không ảnh hưởng** đến giao diện, cấu hình, hay dữ liệu khách đã phê
> duyệt.

## 1. Tổng quan

| Model | Số bản ghi | File CSV nguồn | Có `sre_demo.*` External ID? |
|---|---|---|---|
| `product.brand` | **2** | `01_brands.csv` | ✅ Có |
| `res.partner` (Manufacturer demo) | **2** | `02_manufacturers.csv` | ✅ Có |
| `product.public.category` (Website category) | **3** | `03_website_categories.csv` | ✅ Có |
| `product.template` (Sản phẩm demo) | **6** (1 variant mỗi cái → tạo thêm 6 `product.product`) | `04_products.csv` | ✅ Có |
| **Tổng bản ghi mới** | **13 record chính + 6 product.product phái sinh** | — | **13 External ID cố định** |

## 2. Danh sách đầy đủ (External ID → giá trị khóa)

### 2.1 `product.brand` (2 bản ghi)

| External ID | Name | Description | Partner |
|---|---|---|---|
| `sre_demo.brand_demo_a` | `DemoBrand A [DEMO]` | "Demo brand for SRE catalog testing. Not a real brand. Not for production use. partner_id is intentionally empty per project privacy rule (Risk #19)." | _(empty — Risk #19)_ |
| `sre_demo.brand_demo_b` | `DemoBrand B [DEMO]` | "Demo brand for SRE catalog testing. Not a real brand. Not for production use. partner_id is intentionally empty per project privacy rule (Risk #19)." | _(empty — Risk #19)_ |

### 2.2 `res.partner` (Manufacturer demo, 2 bản ghi)

| External ID | Name | Company Type | Country |
|---|---|---|---|
| `sre_demo.partner_demo_mfg_a` | `DemoMfg A [DEMO]` | `company` | `Vietnam` (External ID `base.vn`) |
| `sre_demo.partner_demo_mfg_b` | `DemoMfg B [DEMO]` | `company` | `Vietnam` |

Lưu ý: 2 partner này **không** đặt `supplier_rank` / `customer_rank`. Chỉ
dùng cho OCA `product_manufacturer.manufacturer_id`. Không ảnh hưởng đến
Purchase hoặc Sale workflow.

### 2.3 `product.public.category` (3 bản ghi)

| External ID | Name | Parent |
|---|---|---|
| `sre_demo.public_cat_demo` | `Demo Catalog [DEMO]` | _(root — không có parent)_ |
| `sre_demo.public_cat_demo_valves` | `Valves [DEMO]` | `sre_demo.public_cat_demo` |
| `sre_demo.public_cat_demo_pumps` | `Pumps [DEMO]` | `sre_demo.public_cat_demo` |

Lưu ý: xóa parent **trước** children sẽ lỗi foreign key. Xóa theo thứ tự
sau: children → parent.

### 2.4 `product.template` (6 bản ghi, mỗi cái 1 variant)

| External ID | Name | SKU (`default_code`) | Type | Brand | Manufacturer | MPN | eCommerce Cat |
|---|---|---|---|---|---|---|---|
| `sre_demo.product_template_demo_v_001` | Demo Valve 001 [DEMO] | `SRE-DEMO-V-001` | consu | `sre_demo.brand_demo_a` | `sre_demo.partner_demo_mfg_a` | `DMV-001` | `sre_demo.public_cat_demo_valves` |
| `sre_demo.product_template_demo_v_002` | Demo Valve 002 [DEMO] | `SRE-DEMO-V-002` | consu | `sre_demo.brand_demo_a` | `sre_demo.partner_demo_mfg_b` | `DMV-002` | `sre_demo.public_cat_demo_valves` |
| `sre_demo.product_template_demo_v_003` | Demo Valve 003 [DEMO] | `SRE-DEMO-V-003` | consu | `sre_demo.brand_demo_b` | `sre_demo.partner_demo_mfg_a` | `DMV-003` | `sre_demo.public_cat_demo_valves` |
| `sre_demo.product_template_demo_p_001` | Demo Pump 001 [DEMO] | `SRE-DEMO-P-001` | consu | `sre_demo.brand_demo_a` | `sre_demo.partner_demo_mfg_a` | `DMP-001` | `sre_demo.public_cat_demo_pumps` |
| `sre_demo.product_template_demo_p_002` | Demo Pump 002 [DEMO] | `SRE-DEMO-P-002` | consu | `sre_demo.brand_demo_b` | `sre_demo.partner_demo_mfg_b` | `DMP-002` | `sre_demo.public_cat_demo_pumps` |
| `sre_demo.product_template_demo_p_003` | Demo Pump 003 [DEMO] | `SRE-DEMO-P-003` | consu | `sre_demo.brand_demo_b` | `sre_demo.partner_demo_mfg_a` | `DMP-003` | `sre_demo.public_cat_demo_pumps` |

Mỗi template sẽ tự động tạo đúng **1** `product.product` (variant mặc
định). Variant không có External ID riêng — nó là dẫn xuất và sẽ bị xóa
cùng template.

Thuộc tính chung của cả 6 sản phẩm:

- `categ_id = product.product_category_goods` (Odoo built-in)
- `uom_id = uom.product_uom_unit`
- `sale_ok = True`, `purchase_ok = True`, `is_published = False`
- `list_price = 0.0`

## 3. Cách xác minh trước khi dọn (chạy trong shell)

```bash
docker compose -p odoo_mechanic exec -T odoo odoo shell -d mechanic_workshop --no-http <<'PY'
# Đếm tất cả bản ghi sẽ bị xóa
records = env['ir.model.data'].search([('module','=','sre_demo')])
print(f"Tổng External ID cần dọn: {len(records)}")
for r in records:
    print(f"  {r.module}.{r.name:42s} -> {r.model}#{r.res_id}")

# Kiểm tra rằng không có bản ghi ngoài dự kiến mang module sre_demo
extra = env['ir.model.data'].search([
    ('module','=','sre_demo'),
    ('name','not in',[
        'brand_demo_a','brand_demo_b',
        'partner_demo_mfg_a','partner_demo_mfg_b',
        'public_cat_demo','public_cat_demo_valves','public_cat_demo_pumps',
        'product_template_demo_v_001','product_template_demo_v_002','product_template_demo_v_003',
        'product_template_demo_p_001','product_template_demo_p_002','product_template_demo_p_003',
    ]),
])
if extra:
    print(f"!! CẢNH BÁO: có {len(extra)} External ID sre_demo.* ngoài danh sách — KHÔNG xóa mù:")
    for r in extra:
        print(f"     {r.module}.{r.name} -> {r.model}#{r.res_id}")
else:
    print("Không có External ID sre_demo.* ngoài danh sách. An toàn để dọn theo INVENTORY.")

# Đếm theo model
from collections import Counter
models = Counter(r.model for r in records)
print("\nPhân bố theo model:")
for m, c in sorted(models.items()):
    print(f"  {m}: {c}")
PY
```

Kỳ vọng khi đã import đủ 4 file:

- Tổng External ID: **13**
- Phân bố: `product.brand=2`, `res.partner=2`, `product.public.category=3`, `product.template=6`

## 4. Quy trình dọn — ưu tiên UI (an toàn nhất)

**Bước 4.1 — Liệt kê tất cả External ID demo**:

`Settings → Technical → External Identifiers` (bật Developer Mode trước).

Ô search gõ `sre_demo` (chỉ module) hoặc `sre_demo.` (full prefix) → sẽ
ra đúng **13** dòng sau khi import.

**Bước 4.2 — Kiểm tra thật sự là bản ghi demo**:

Mở từng dòng, xác nhận `Name` hoặc `Display Name` chứa `[DEMO]` hoặc
bắt đầu bằng `Demo*`. Nếu có bản ghi KHÔNG phải demo nhưng trùng
External ID, dừng lại và báo cáo.

**Bước 4.3 — Xóa có thứ tự**:

UI `External Identifiers` không tự xếp thứ tự theo foreign key. Dùng
cách sau:

1. **Xóa sản phẩm trước** (vì chúng tham chiếu Brand/Manufacturer/Category):
   Lọc External ID bắt đầu bằng `sre_demo.product_template_demo_*`,
   chọn tất cả, Action → `Delete` (tick cả "Delete records" để xóa
   cả record product.template + product.product phái sinh + ir.model.data).
2. **Xóa website category** (children trước):
   Lọc `sre_demo.public_cat_demo_*`, chọn cả 3, Delete (bao gồm
   `public_cat_demo_valves`, `public_cat_demo_pumps` trước
   `public_cat_demo`).
3. **Xóa Brand**: lọc `sre_demo.brand_demo_*`, chọn 2, Delete.
4. **Xóa Manufacturer partner**: lọc `sre_demo.partner_demo_mfg_*`,
   chọn 2, Delete. (Sẽ xóa cả `ir.model.data`.)

**Bước 4.4 — Verify**:

```bash
docker compose -p odoo_mechanic exec -T odoo odoo shell -d mechanic_workshop --no-http <<'PY'
print("External ID sre_demo còn lại:", env['ir.model.data'].search_count([('module','=','sre_demo')]))
print("Brand records còn 'DemoBrand' trong tên:", env['product.brand'].search_count([('name','ilike','DemoBrand')]))
print("Manufacturer records còn 'DemoMfg':", env['res.partner'].search_count([('name','ilike','DemoMfg')]))
print("Product templates còn '[DEMO]' trong tên:", env['product.template'].search_count([('name','ilike','[DEMO]')]))
print("Website categories còn '[DEMO]' trong tên:", env['product.public.category'].search_count([('name','ilike','[DEMO]')]))
PY
```

Tất cả phải trả về **0**.

## 5. Quy trình dọn — script shell (1 phát, nguyên tử)

> **CẢNH BÁO**: Script này xóa trực tiếp qua shell. Chỉ chạy khi đã
> qua bước 4.1–4.2 xác nhận. Backup database trước khi chạy (xem mục 6).

```bash
docker compose -p odoo_mechanic exec -T odoo odoo shell -d mechanic_workshop --no-http <<'PY'
import logging
_logger = logging.getLogger(__name__)

# Thứ tự xóa: products -> categories -> brands -> manufacturers
# Lý do: products tham chiếu các bảng khác (FK), manufacturers là leaf.
ORDER = [
    'product.template',
    'product.public.category',
    'product.brand',
    'res.partner',
]

# Lấy tất cả External ID sre_demo.* (chỉ trong danh sách này)
EXPECTED = {
    'product.template': [
        'product_template_demo_v_001','product_template_demo_v_002','product_template_demo_v_003',
        'product_template_demo_p_001','product_template_demo_p_002','product_template_demo_p_003',
    ],
    'product.public.category': [
        'public_cat_demo','public_cat_demo_valves','public_cat_demo_pumps',
    ],
    'product.brand': ['brand_demo_a','brand_demo_b'],
    'res.partner': ['partner_demo_mfg_a','partner_demo_mfg_b'],
}

xml_ids = env['ir.model.data'].search([
    ('module','=','sre_demo'),
    ('name','in',[n for ns in EXPECTED.values() for n in ns]),
])
by_model = {}
for x in xml_ids:
    by_model.setdefault(x.model, []).append(x)

deleted = 0
for model in ORDER:
    xids = by_model.get(model, [])
    if not xids:
        continue
    records = env[model].browse([x.res_id for x in xids])
    # Bỏ qua record đã bị xóa trước đó (cascade có thể đã xóa)
    records = records.exists()
    _logger.info("Deleting %d %s records", len(records), model)
    # Với product.template, unlink sẽ cascade xóa product.product
    records.unlink()
    # Sau khi unlink, ir.model.data rows sẽ tự cascade xóa theo
    deleted += len(records)

env.cr.commit()
print(f"Đã xóa {deleted} bản ghi + các bản ghi phái sinh (ir.model.data cascade).")
print("External ID sre_demo còn lại:", env['ir.model.data'].search_count([('module','=','sre_demo')]))
print("Brand records còn 'DemoBrand' trong tên:", env['product.brand'].search_count([('name','ilike','DemoBrand')]))
PY
```

Sau khi chạy, mọi dòng `còn lại` phải in **0**.

## 6. Backup trước khi dọn (khuyến cáo)

Dù stack dùng volume namespaced, vẫn backup database trước khi xóa hàng
loạt — cho cả 2 phương án UI và shell:

```bash
# Tạo backup file
docker compose -p odoo_mechanic exec -T db pg_dump -U odoo mechanic_workshop \
    > /home/khoa/Company/odoo_mechanic/backups/mechanic_workshop_before_demo_cleanup_$(date +%Y%m%d_%H%M%S).sql
```

(AGENTS.md §3 rule 8: chỉ xóa sau khi có backup verified.)

Khôi phục:

```bash
docker compose -p odoo_mechanic exec -T db psql -U odoo -d mechanic_workshop < backups/mechanic_workshop_before_demo_cleanup_*.sql
```

## 7. Cái gì KHÔNG bị ảnh hưởng khi dọn

| Hạng mục | Bị động? | Ghi chú |
|---|---|---|
| Giao diện (theme `theme_vehicle`, asset bundles, view overrides) | ❌ Không | Không có record nào trong INVENTORY này thuộc `ir.ui.view`, `ir.ui.menu`, `website.theme` |
| Cấu hình hệ thống (`ir.config_parameter`, `res.company`, `res.currency`) | ❌ Không | Manufacturer demo là `res.partner`, không phải `res.company` |
| Modules OCA đã cài (`product_brand`, `product_manufacturer`, `product`, `contacts`, `website_sale`, ...) | ❌ Không | Module state không liên quan đến External ID instance data |
| Dữ liệu khách đã phê duyệt (bất kỳ record nào KHÔNG có `sre_demo.*` External ID) | ❌ Không | Script xóa lọc chính xác theo `module='sre_demo'` |
| Ảnh / tài liệu đính kèm (`ir.attachment`) | ❌ Không | Bộ demo không tạo attachment nào |
| Sales / Purchase / Invoice đã phát sinh | ❌ Không | Bộ demo dùng `type=consu`, không có giá, không có stock — không thể tạo sale.order/purchase.order/invoice |
| Cron job, automated action, server action | ❌ Không | Không tạo |
| OCA `product.brand.partner_id` records có sẵn (Risk #19) | ❌ Không | Tất cả 2 brand đều có `partner_id = False` từ đầu (per file) |
| Views riêng của OCA (form/kanban/list `product.brand`) | ❌ Không | Đó là view của module, không phải record instance |

## 8. Làm gì nếu quên không backup?

- Stack `odoo_mechanic` có named volume `odoo_mechanic_db` chứa DB
  PostgreSQL. Backup volume trước khi xóa có thể tốn disk; xem
  `scripts/backup_db.sh` nếu có, hoặc dùng `pg_dump` ở trên.
- Nếu đã xóa mà cần khôi phục, chỉ có cách restore từ backup hoặc
  re-import lại 4 CSV.

## 9. Trạng thái cập nhật

| Lần cập nhật | Người cập nhật | Thay đổi |
|---|---|---|
| 2026-09-07 | agent | Tạo file, 13 External IDs, tiền tố `sre_demo.` |

Khi thay đổi bộ demo (thêm/xóa record, đổi prefix), cập nhật bảng này
để tránh INVENTORY lệch với thực tế.
