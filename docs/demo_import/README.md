# Bộ CSV sản phẩm DEMO — SRE Commercial

> **Đã chuẩn bị cấu trúc. CHƯA thử import vào Odoo.** Trước khi import, đọc kỹ
> phần "Điều kiện cần" và "Kiểm tra trước khi import".

Mục đích: kiểm thử catalog, Brand, Manufacturer, MPN và luồng RFQ trên
Odoo 19. **Không phải dữ liệu kỹ thuật thật của khách hàng.** Mọi tên, mã
và thông số đều có dấu hiệu `[DEMO]` hoặc tiền tố `DEMO-` / `DMV-` / `DMP-`.

## Điều kiện cần

| # | Điều kiện | Cách kiểm tra |
|---|---|---|
| 1 | Odoo 19 đang chạy tại `http://localhost:8080` | Mở trình duyệt, đăng nhập admin |
| 2 | Database `mechanic_workshop` | Trang đăng nhập hiển thị đúng tên DB |
| 3 | Module `product_brand` đã cài | Settings → Apps → search "Product Brand Manager" → phải ở trạng thái **Installed** |
| 4 | Module `product_manufacturer` đã cài | Settings → Apps → search "Product Manufacturer" → phải ở trạng thái **Installed** |
| 5 | Module `website_sale` đã cài | Cùng cách trên |
| 6 | Quyền Administration: Settings / Sales / Inventory / Website | User hiện tại có quyền truy cập Settings |
| 7 | File CSV không bị sửa encoding | Mở bằng Notepad VS Code, đảm bảo hiển thị đúng tiếng Việt và dấu `[DEMO]` |

Nếu `product_brand` hoặc `product_manufacturer` chưa cài:

- `product_brand`: Settings → Apps → Update Apps List → search "Product Brand Manager" → Install. **Không bắt buộc** cho file `01_brands.csv` (nó tạo brand độc lập), **bắt buộc** cho `04_products.csv` (cần field `product_brand_id`).
- `product_manufacturer`: Settings → Apps → Update Apps List → search "Product Manufacturer" → Install. **Bắt buộc** cho `04_products.csv` (cần field `manufacturer_id`, `manufacturer_pref`). Nếu chưa cài, hệ thống sẽ báo lỗi khi mapping cột; bỏ qua 2 cột này sẽ tạo được sản phẩm nhưng **không có MPN/Manufacturer**.

## Kiểm tra trước khi import (chạy trong shell)

```bash
docker compose -p odoo_mechanic exec -T odoo odoo shell -d mechanic_workshop --no-http <<'PY'
# 1. Modules
for m in env['ir.module.module'].search([('name','in',['product_brand','product_manufacturer'])]):
    print(f"{m.name}: state={m.state} version={m.installed_version}")

# 2. External IDs chưa tồn tại (0 = OK)
ids = ['sre_demo.brand_demo_a','sre_demo.brand_demo_b',  # BẮT BUỘC: import 01_brands.csv trước khi sang 04_products.csv
       'sre_demo.partner_demo_mfg_a','sre_demo.partner_demo_mfg_b',
       'sre_demo.public_cat_demo','sre_demo.public_cat_demo_valves','sre_demo.public_cat_demo_pumps',
       'sre_demo.product_template_demo_v_001','sre_demo.product_template_demo_v_002','sre_demo.product_template_demo_v_003',
       'sre_demo.product_template_demo_p_001','sre_demo.product_template_demo_p_002','sre_demo.product_template_demo_p_003']
collisions = [(x, env['ir.model.data'].search([('module','=',x.split('.')[0]),('name','=',x.split('.')[1])], limit=1))
              for x in ids if env['ir.model.data'].search_count([('module','=',x.split('.')[0]),('name','=',x.split('.')[1])])]
print(f"collisions: {collisions}")

# 3. SKUs chưa tồn tại
skus = ['SRE-DEMO-V-001','SRE-DEMO-V-002','SRE-DEMO-V-003','SRE-DEMO-P-001','SRE-DEMO-P-002','SRE-DEMO-P-003']
print(f"sku conflicts: {env['product.product'].search_count([('default_code','in',skus)])}")
PY
```

Kết quả kỳ vọng:

- `product_brand`: `installed`, version `19.0.1.0.0`
- `product_manufacturer`: `installed`, version `19.0.1.0.0`
- `collisions: []`
- `sku conflicts: 0`

## Thứ tự import

Import theo thứ tự sau. Mỗi file phải import thành công trước khi sang file
tiếp theo.

### Bước 1 — `01_brands.csv` (2 brand)

**Đường dẫn trong UI**: `Sales → Configuration → Product Brands` → menu
`Action ⚙ → Import records` (hoặc `Favorites → Import`).

**Import**:

1. Tải file `01_brands.csv` lên.
2. Để mapping **tự động** (Odoo sẽ match cột `id`, `name`, `description` với field `External ID`, `Name`, `Description`).
3. Nhấn **Test** trước; phải thấy dòng xanh "Everything seems valid".
4. Nhấn **Import**.

**Mapping cột**:

| CSV column | Odoo field | Kiểu |
|---|---|---|
| `id` | External ID | Chuỗi — phải có dạng `module.name` |
| `name` | Name | Char, required |
| `description` | Description | Text (cho phép xuống dòng) |

### Bước 2 — `02_manufacturers.csv` (2 đối tác)

**Đường dẫn trong UI**: `Contacts → Action ⚙ → Import records`.

**Import**:

1. Tải file `02_manufacturers.csv`.
2. Nếu Odoo không tự nhận `company_type`, đổi sang **Selection** và
   chọn value `company`. Nếu không thấy, giữ mặc định `is_company=True`
   cũng được — cả hai đều đánh dấu là công ty.
3. `country_id/id` cột sẽ được map thành **Country** (`res.country`); gõ
   `base.vn` để match External ID.
4. **Test** → **Import**.

**Mapping cột**:

| CSV column | Odoo field | Kiểu |
|---|---|---|
| `id` | External ID | Chuỗi |
| `name` | Name | Char |
| `company_type` | Company Type | Selection (`person` / `company`) |
| `country_id/id` | Country | Many2one (`res.country`) theo External ID |

### Bước 3 — `03_website_categories.csv` (3 danh mục)

**Đường dẫn trong UI**: `Website → eCommerce → Product Categories` →
`Action ⚙ → Import records`. (Nếu menu này không có, dùng
`Inventory → Configuration → Products → Product Categories` cho nội bộ;
**phải** dùng `Website → eCommerce → Product Categories` cho danh mục
website — đây là model `product.public.category`, khác với
`product.category` nội bộ.)

**Import**:

1. Tải file `03_website_categories.csv`.
2. `parent_id/id` cột — chỉ 2 dòng dưới cùng có giá trị; dòng đầu
   (root) để trống.
3. **Test** → **Import**.

**Mapping cột**:

| CSV column | Odoo field | Kiểu |
|---|---|---|
| `id` | External ID | Chuỗi |
| `name` | Name | Char |
| `parent_id/id` | Parent Category | Many2one theo External ID (để trống = root) |

### Bước 4 — `04_products.csv` (6 sản phẩm)

**Đường dẫn trong UI**: `Inventory → Master Data → Products` →
`Action ⚙ → Import records`.

**Import**:

1. Tải file `04_products.csv`.
2. Odoo nhận các cột có hậu tố `/id` là M2O qua External ID. (Hậu tố `:id` cũng hoạt động ở API `load()` nhưng mapping UI của Odoo 19 chỉ tự nhận dạng `/id`. Đổi sang `/id` để khớp cả UI lẫn API.)
3. Đặc biệt kiểm tra:
   - `categ_id/id` → map sang **Product Category** (`product.category`), External ID `product.product_category_goods`.
   - `uom_id/id` → **Unit of Measure** (`uom.uom`), External ID `uom.product_uom_unit`.
   - `product_brand_id/id` → **Brand** (`product.brand`), External ID `sre_demo.brand_demo_*`.
   - `manufacturer_id/id` → **Manufacturer** (`res.partner`), External ID `sre_demo.partner_demo_mfg_*` (chỉ có nếu `product_manufacturer` đã cài).
   - `public_categ_ids/id` → **eCommerce Categories** (`product.public.category`), External ID `sre_demo.public_cat_demo_*`.
4. `description` cột là HTML; Odoo sẽ nhận diện nếu bạn để mặc định.
5. `manufacturer_pref` cột là **Manufacturer Product Code** (MPN); chỉ có nếu `product_manufacturer` đã cài.
6. **Test** → nếu có dòng đỏ "missing field" liên quan đến manufacturer, xem mục "Nếu thiếu module".
7. **Import**.

**Lưu ý — cột `product_brand_id/id`**:

- Cột này dùng **External ID** như các cột M2O/M2M khác.
- Giá trị trong CSV là External ID (`sre_demo.brand_demo_a` hoặc
  `sre_demo.brand_demo_b`).
- Nếu bạn import theo thứ tự 01 → 02 → 03 → 04, brand đã có sẵn khi
  sang bước 4 và import thành công.
- Nếu bạn làm theo cách khác (ví dụ nhảy thẳng sang 04 sau khi mới
  import 02 + 03), External ID brand chưa tồn tại → Odoo báo lỗi.
  Trong trường hợp đó: import `01_brands.csv` trước, hoặc chạy shell
  command sau để tạo brand với External ID rồi retry:

```bash
docker compose -p odoo_mechanic exec -T odoo odoo shell -d mechanic_workshop --no-http <<'PY'
Brand = env['product.brand']
IMD = env['ir.model.data']
for name, ext in [('DemoBrand A [DEMO]', 'brand_demo_a'), ('DemoBrand B [DEMO]', 'brand_demo_b')]:
    if not IMD.search([('module','=','sre_demo'),('name','=',ext)]):
        b = Brand.create({'name': name, 'description': 'Demo brand for SRE catalog testing. Not a real brand. Not for production use.'})
        IMD.create({'module':'sre_demo','name':ext,'model':'product.brand','res_id':b.id})
env.cr.commit()
print('Brands ready:', Brand.search([('name','ilike','DemoBrand')]).mapped('name'))
PY
```

**Mapping cột**:

| CSV column | Odoo field | Model | Kiểu / Ghi chú |
|---|---|---|---|
| `id` | External ID | — | Chuỗi, format `module.name` |
| `name` | Name | product.template | Char, required |
| `default_code` | Internal Reference | product.template (sync sang product.product) | Char — SRE SKU |
| `type` | Product Type | product.template | Selection: `consu` (Hàng hóa — không tồn kho), `product` (Storable), `service` |
| `categ_id/id` | Product Category | product.category | Many2one theo External ID |
| `uom_id/id` | Unit of Measure | uom.uom | Many2one — `uom.product_uom_unit`. **Odoo 19 đã bỏ `uom_po_id`** — product chỉ còn 1 đơn vị chung cho cả bán và mua. |
| `sale_ok` | Can be Sold | product.template | Boolean |
| `purchase_ok` | Can be Purchased | product.template | Boolean |
| `is_published` | Is Published | product.template | Boolean — `False` (không xuất bản) |
| `list_price` | Sales Price | product.template | Float — `0.0` (cập nhật sau) |
| `product_brand_id/id` | Brand | product.brand | Many2one theo External ID — yêu cầu `product_brand` |
| `manufacturer_id/id` | Manufacturer | res.partner | Many2one theo External ID — yêu cầu `product_manufacturer` |
| `manufacturer_pref` | Manufacturer Product Code | product.template | Char (MPN) — yêu cầu `product_manufacturer` |
| `public_categ_ids/id` | eCommerce Categories | product.public.category | Many2many theo External ID |
| `description` | Description | product.template | HTML (cho phép xuống dòng trong ô quote) |

**Cách OCA `product_manufacturer` xử lý 1-variant template**:

Module OCA compute field `manufacturer_id` dựa trên
`product_variant_ids`. Khi chỉ có **1 variant duy nhất** (trường hợp của
bộ demo này), import trên `product.template` sẽ tự động propagate xuống
`product.product` qua `_inverse_manufacturer_info`. **Không cần file
variant riêng** cho bộ 6 sản phẩm này.

## Nếu thiếu module

| Tình huống | Cách xử lý |
|---|---|
| `product_brand` chưa cài | Bỏ cột `product_brand_id` khi mapping; sản phẩm vẫn tạo được nhưng Brand sẽ trống. Có thể cập nhật sau khi cài module. |
| `product_manufacturer` chưa cài | Bỏ 2 cột `manufacturer_id/id` và `manufacturer_pref`; sản phẩm tạo được nhưng MPN/Manufacturer sẽ trống. Cài module rồi update lại bằng cùng External ID (xem "Import lại"). |
| `product` chưa cài | Không thể import; phải cài `product` (đã có sẵn trong stack mặc định). |
| `website_sale` chưa cài | Bỏ cột `public_categ_ids/id`; sản phẩm vẫn tạo nhưng không nằm trong catalog website. |

## Cách xác nhận import đúng

Sau khi import xong cả 4 file, chạy lại các bước kiểm tra sau trong UI:

### Tổng số

- `Sales → Configuration → Product Brands`: **2** records (DemoBrand A, DemoBrand B)
- `Contacts`: lọc `Company Type = Company` và tên chứa "DemoMfg" → **2** records (DemoMfg A, DemoMfg B)
- `Website → eCommerce → Product Categories`: **3** records (Demo Catalog, Valves, Pumps)
- `Inventory → Master Data → Products`: lọc tên chứa `[DEMO]` → **6** records

### Từng sản phẩm

Với mỗi sản phẩm (mở form view), kiểm tra:

| Field | Giá trị kỳ vọng cho V001 (ví dụ) |
|---|---|
| Name | `Demo Valve 001 [DEMO]` |
| Internal Reference (SKU) | `SRE-DEMO-V-001` |
| Product Type | `Hàng hóa` (consu) |
| Product Category | `Goods` |
| Unit of Measure / Purchase UoM | `Units` |
| Can be Sold / Can be Purchased | checked |
| Is Published | **không** checked (tích) |
| Sales Price | `0.00` |
| Brand | `DemoBrand A [DEMO]` |
| Manufacturer | `DemoMfg A [DEMO]` |
| Manufacturer Product Code (MPN) | `DMV-001` |
| eCommerce Categories | `Valves [DEMO]` |
| Description | chứa chuỗi `DEMO. Specification data is illustrative only` |

### Variant

Mở tab **Variants** (hoặc `Inventory → Master Data → Products →
Variants` lọc theo Attribute → không có): **1 variant duy nhất** với
cùng `default_code = SRE-DEMO-V-001`.

Tab **General Information → Sales → Manufacturer** (chỉ có khi
`product_manufacturer` cài) phải hiện `DemoMfg A [DEMO]` và
`DMV-001`.

### Brand/Manufacturer không lộ supplier

`Sales → Configuration → Product Brands → DemoBrand A`: tab
**Internal Notes** / form, xác nhận trường **Partner** trống. (Risk
#19 trong spec; test này sẽ tự động thành phần
`scripts/agent_check.sh` sau khi Sprint 1 thêm rule.)

## Import lại để cập nhật (không tạo trùng)

Vì mỗi record có External ID ổn định (`sre_demo.*`), bạn có thể:

1. Sửa file CSV (ví dụ: thêm MPN, đổi Brand, sửa description).
2. Vào cùng menu Import → tải file lên.
3. Khi Odoo hỏi, chọn **Use the same External ID** (hoặc để mặc định
   với checkbox "Update if exists").
4. **Test** xem Odoo báo bao nhiêu dòng "update" / "create".
5. **Import**.

Kết quả:

- Cùng External ID → **update** record đó.
- External ID mới → tạo record mới.
- Không có External ID → tạo mới nhưng **không tái sử dụng được** sau này (khuyến cáo luôn kèm cột `id`).

## Những chức năng KHÔNG thể kiểm thử với bộ dữ liệu này

| Chức năng | Lý do |
|---|---|
| Multi-field search theo Brand (OCA custom) | Cần module `sre_commercial_search` (Sprint 1); hiện chỉ có OCA `product_brand` |
| Multi-field search theo Manufacturer name | Cần `sre_commercial_search` |
| Search theo OEM PN / MPN | Cần `sre_commercial_pim` (chưa có model `sre.oem.pn`) |
| Technical filter per Product Family | Cần `sre_commercial_catalog` (chưa có model `sre.product.family`) |
| Brand/Manufacturer combo filter | Chưa có filter UI cho OCA `product_brand` |
| Cross Reference (Alternative / Replacement / Related) | Cần `sre_commercial_crossref` |
| Compatibility Matrix | Cần `sre_commercial_compatibility` |
| Document Rights gating | Cần `sre_commercial_documents` |
| RFQ submit → CRM Lead | Cần `sre_commercial_rfq` |
| Boiler Part Finder | Cần `sre_commercial_boiler` |
| Industry / Application taxonomy | Cần `sre_commercial_taxonomy` |
| Customer Portal, Contract Pricing | Cần `sre_commercial_portal` (Sprint 4) |
| Technical spec-driven search/filter | Thông số chỉ nằm trong description; chưa có model spec nào |
| Stock / Inventory / Re-order | `type=consu`, không theo dõi tồn kho |
| Pricing display trên website | `list_price=0.0`; website sẽ không hiển thị giá mà chỉ CTA RFQ (nếu module RFQ có sẵn) |
| Public visibility | `is_published=False`; sản phẩm chưa hiển thị trên `/shop` |

## Trạng thái kiểm thử (evidence)

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Cú pháp CSV (4 file) | ✅ Đã kiểm tra bằng `csv.reader` Python | 0 lỗi parse; 13 External IDs unique; 0 trùng giữa các file |
| External ID uniqueness | ✅ | 13 ids đếm đúng, không trùng |
| Cross-file references | ✅ | 7 External ID được tham chiếu trong `04_products.csv` đều có definition trong file 01/02/03 |
| Khớp schema Odoo thực tế | ✅ | Field tồn tại trên `product.template` (đã verify qua `env['product.template']._fields`) |
| Khớp schema OCA `product_brand` | ✅ | `product_brand_id` (M2O product.brand) có mặt; module `product_brand` state=installed |
| Khớp schema OCA `product_manufacturer` | ✅ | `manufacturer_id`, `manufacturer_pref` có mặt; module `product_manufacturer` state=installed |
| Header `/id` syntax → UI auto-maps sang External ID | ✅ | `imp._get_mapping_suggestion('country_id/id', ...)` trả về `['country_id','id']` (External ID mode) — đã test với cả 4 file |
| Header `:id` syntax → UI auto-maps sang External ID | ❌ | `_get_mapping_suggestion('country_id:id', ...)` trả về `['country_id']` (name lookup) — đã fix, đổi sang `/id` |
| End-to-end import (qua API `load()` với header `/id`) | ✅ | Tạo 3 sản phẩm demo + brand + manufacturer + MPN + public category thành công, sau đó cleanup về 0 |
| Không ghi đè bản ghi hiện có | ✅ | `ir.model.data` không có 13 External IDs trên (0 collisions) |
| Không tạo tồn kho | ✅ | `type=consu`, không tạo `product.template` với `type=product`, không có quy trình nhập |
| Không tạo nhà cung cấp | ✅ | Không tạo `res.partner` với `supplier_rank>0`; chỉ tạo 2 partner demo cho manufacturer |
| Không tạo OEM PN / cross-ref / compatibility | ✅ | Không import vào `sre.oem.pn`, `sre.product.crossref`, `sre.product.compatibility` |
| Không tải ảnh / tài liệu | ✅ | Không có cột `image_1920`, không tạo `ir.attachment` |

**Chưa xác minh qua UI** (cần người dùng chạy tay):

- Import thực tế qua UI wizard (ký tự, format preview, dialog lỗi) → kết quả `state=done` không lỗi
- Sau import: 6 products đúng như bảng "Từng sản phẩm" (đã verify cấu trúc; chưa verify UX UI)
- Brand filter hiển thị trên `/shop` (khi bật `is_published=True`)
- Manufacturer field xuất hiện trên form sản phẩm

Lưu ý: phần "E2E qua API `load()`" đã chạy thành công nhưng tự cleanup; DB hiện không có bản ghi demo nào.

## Cấu trúc file

```
docs/demo_import/
├── README.md                    ← file này
├── 01_brands.csv                 (2 dòng) Brand demo
├── 02_manufacturers.csv          (2 dòng) Manufacturer demo (res.partner)
├── 03_website_categories.csv     (3 dòng) Danh mục website
└── 04_products.csv               (6 dòng) Sản phẩm demo (3 van + 3 bơm)
```

Tất cả External ID đều có tiền tố `sre_demo.` để tránh xung đột với dữ
liệu khác và cho phép xóa hàng loạt nếu cần. **Tất cả 13 bản ghi demo
được liệt kê trong `INVENTORY.md`** kèm script xóa an toàn khi cần dọn.
