# Hướng Dẫn Kiểm Thử (Testing Guide) — Product Classification Engine (Part 2)

Tài liệu này cung cấp hướng dẫn chi tiết cách kiểm thử toàn diện từ **Phase 1** đến **Phase 4** của module `mechanic_workshop` trên Odoo 19.

---

## 1. Tổng Quan Các Phase Đã Hoàn Thành

| Phase | Tên chức năng | Mục tiêu cốt lõi |
|---|---|---|
| **Phase 1** | Taxonomy Master Data | Chuỗi phân cấp 4 tầng: Pillar (L1) $\rightarrow$ Category (L2) $\rightarrow$ Family (L3) $\rightarrow$ Type (L4) & UI Quản trị Admin. |
| **Phase 2** | Attribute Profile Metadata | 5 cờ metadata thuộc tính: `is_required`, `is_filter_shown`, `is_display_shown`, `creates_variant`, `value_ids`. |
| **Phase 3** | Catalog Routing & Navigation | Dynamic URLs `/sre/catalog/category/<slug>`, 301 redirect từ `/shop`, Breadcrumb 4 cấp động, McMaster Sub-Chips. |
| **Phase 4** | Dynamic Filter Engine 2 Tầng | Cô lập hoàn toàn: Toàn sàn (All Categories) chỉ có Global Filters; Scope kỹ thuật tự động merge Attribute Profiles để sinh checkbox filters động. |

---

## 2. Hướng Dẫn Kiểm Thử Trên Giao Diện Web (UI Browser)

### 2.1. Kiểm thử Phase 1 & 2 trên Backend Admin (Odoo Backend)
1. **Truy cập Backend**:
   - URL: `http://localhost:8080/web`
   - Đăng nhập tài khoản Administrator.
2. **Kiểm tra Danh mục cấp 2 (Product Categories)**:
   - Vào menu: **SRE Technical Catalog** $\rightarrow$ **Pillars & Taxonomy** $\rightarrow$ **Product Categories**.
   - Kiểm tra danh sách: Phải hiển thị các Category với cột *Name*, *Slug*, *Pillar*, *Sequence*, *Active*.
   - Tạo mới 1 Category:
     - Nhấn **New**.
     - Nhập Tên: `Centrifugal Pumps`, Slug: `centrifugal-pumps`, chọn Pillar: `Pumps`.
     - Lưu lại và kiểm tra xem slug có tự sinh và hiển thị đúng không.
3. **Kiểm tra Loại sản phẩm cấp 4 (Product Types)**:
   - Vào menu: **SRE Technical Catalog** $\rightarrow$ **Pillars & Taxonomy** $\rightarrow$ **Product Types**.
   - Tạo mới 1 Product Type:
     - Nhập Tên: `Multi-Stage Type A`, Slug: `multistage-type-a`, chọn Family: `Vertical Multistage Centrifugal Pumps`.
     - Lưu lại thành công.
4. **Kiểm tra Metadata trên Attribute Profile (Phase 2)**:
   - Vào menu: **SRE Technical Catalog** $\rightarrow$ **Pillars & Taxonomy** $\rightarrow$ **Attribute Profiles**.
   - Mở một Profile (ví dụ: *Centrifugal Pump Profile*).
   - Kiểm tra bảng thuộc tính `Attributes`:
     - Phải có đầy đủ các cột checkbox: **Mandatory** (`is_required`), **Show in Filter** (`is_filter_shown`), **Show in Specs** (`is_display_shown`), **Creates Variant** (`creates_variant`).
     - Tích chọn/bỏ chọn và nhấn Lưu $\rightarrow$ Hệ thống lưu trữ chính xác trạng thái checkbox.

---

### 2.2. Kiểm thử Phase 3 & 4 trên Website Storefront

#### A. Kiểm thử Tầng 1: Toàn sàn (All Categories)
1. Truy cập: `http://localhost:8080/sre/catalog`
2. **Quan sát thanh Sidebar (Global Filters)**:
   - Phải có dropdown **Brand** (Hãng sản xuất).
   - Phải có dropdown **Industry** (Ngành công nghiệp: Food & Beverage, Chemical, Manufacturing, v.v.).
   - Phải có dropdown **Application** (Ứng dụng: Steam System, Boiler Water Level Control, HVAC Control, v.v.).
   - **TIÊU CHÍ QUAN TRỌNG (Phase 4)**: Khối `Technical specifications` (các thanh trượt Áp suất, Nhiệt độ, Lưu lượng) **KHÔNG ĐƯỢC PHÉP HIỂN THỊ** ở trang này.
3. **Quan sát thanh Quick-Chips**:
   - Chỉ hiển thị *Product Line* và *Manufacturer*.
   - Hàng chip *Pressure Class: PN 16 / PN 25 / PN 40* **PHẢI ẨN** ở trang toàn sàn.
4. **Thử nghiệm tương tác**:
   - Chọn một Industry từ dropdown (ví dụ: `Food & Beverage`) $\rightarrow$ Trang tự động reload và lọc đúng các sản phẩm của ngành đó.

#### B. Kiểm thử Tầng 2: Đi vào Category Scope (Phase 3 & Phase 4)
1. Truy cập: `http://localhost:8080/sre/catalog/category/centrifugal-pumps`
2. **Kiểm tra Header & Breadcrumb (Phase 3)**:
   - Tiêu đề H1: Hiển thị đúng `Centrifugal Pumps`.
   - Breadcrumb: Hiển thị đúng 3 cấp clickable:
     `Home / Catalog / Pumps / Centrifugal Pumps`
   - Thanh Sub-chips McMaster: Hiển thị nút `All Pumps` và nút chip `Centrifugal Pumps` (có badge số lượng sản phẩm).
3. **Kiểm tra Dynamic Technical Filters (Phase 4)**:
   - Sidebar tự động hiển thị khối **Technical specifications** (Operating Pressure, Temperature, Flow rate).
   - Sidebar tự động hiển thị nhóm thuộc tính động được merge từ profile của các dòng bơm con (ví dụ: nhóm checkbox `Impeller Material` với giá trị `SS304`, `SS316`).
   - Tích chọn checkbox `SS304` $\rightarrow$ Danh sách sản phẩm được lọc theo thuộc tính này.
4. **Kiểm tra 301 Redirect (Phase 3)**:
   - Mở trình duyệt gõ: `http://localhost:8080/shop/category/centrifugal-pumps`
   - Quan sát thanh địa chỉ $\rightarrow$ Trình duyệt tự động chuyển hướng 301 sang `http://localhost:8080/sre/catalog/category/centrifugal-pumps`.

#### C. Kiểm thử đi sâu vào Family Scope (Phase 3)
1. Truy cập: `http://localhost:8080/sre/catalog/family/vertical-multistage-pumps`
2. **Kiểm tra Breadcrumb 4 tầng hoàn chỉnh**:
   - Breadcrumb hiển thị:
     `Home / Catalog / Pumps / Centrifugal Pumps / Vertical Multistage Centrifugal Pumps`
   - Click vào `Centrifugal Pumps` $\rightarrow$ Quay lại trang Category.
   - Click vào `Pumps` $\rightarrow$ Quay lại trang Pillar.

#### D. Kiểm thử Chi Tiết Sản Phẩm (Phase 5)
1. Truy cập: `http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5`
2. **Kiểm tra Product identification**:
   - Trường **Category**: Hiển thị link `Centrifugal Pumps` dẫn về catalog category.
   - Trường **Product type**: Hiển thị Level 4 `Vertical Inline Multi-Stage`.
3. **Kiểm tra Phân Nhóm Thông Số Kỹ Thuật (Grouped Technical Specifications)**:
   - Nhóm **Key Specifications**: Hiển thị bảng thông số trọng yếu:
     - `Operating Pressure`: 1.0 – 25.0 bar
     - `Operating Temperature`: -20 to 120 °C
     - `Operating Flow Rate`: 5.0 – 60.0 m³/h
     - `Product Type`: Vertical Inline Multi-Stage
     - `Impeller Material`: SS304 (`is_required=True`)
   - Nhóm **Additional Specifications**: Hiển thị bảng thông số tùy chọn mở rộng:
     - `Flange Standard`: DIN EN 1092-2 PN25 (`is_required=False`)

#### E. Kiểm thử Dữ liệu RFQ Đầy Đủ & Ghi chú Kỹ thuật (Phase 6)
1. Thêm sản phẩm vào RFQ từ trang sản phẩm (nhập ghi chú vận hành).
2. Mở `/rfq`:
   - Xác nhận mỗi dòng sản phẩm hiển thị **SKU**, **MPN**, **Brand**, **Product Type**.
   - Trường nhập **Line specs / operating notes** cho phép nhập ghi chú theo từng dòng.
3. Trong Admin Backend (`Sales -> Customer RFQs`):
   - Mở RFQ vừa tạo: Xác nhận bảng dòng sản phẩm có đủ các cột `SKU`, `MPN`, `Brand`, `Model`, `Technical Notes`.
   - Bấm nút **Create Quotation**: Báo giá được tạo và nội dung ghi chú kỹ thuật được chuyển tự động vào mô tả dòng báo giá (`sale.order.line`).

#### F. Kiểm thử Nghiệm Thu Golden Sample Bơm (Phase 7 & 8)
Thực hiện 6 Acceptance Tests theo đúng quy định tại Mục XVIII của tài liệu:
- **Test 1**: Tạo Product Family trực tiếp trên Backend UI không cần code ➔ Lưu thành công.
- **Test 2**: Gắn Attribute Profile vào Family ➔ Lưu thành công.
- **Test 3**: Sửa đổi metadata thuộc tính (`is_filter_shown`, `is_display_shown`) trên Profile ➔ Lưu thành công.
- **Test 4**: Vào catalog của Family/Pillar ➔ Bộ lọc cập nhật động theo đúng Profile đã cấu hình.
- **Test 5**: Mở trang chi tiết sản phẩm ➔ Bảng thông số cập nhật động theo Profile.
- **Test 6**: Kiểm tra RFQ lưu trữ đầy đủ SKU, MPN, Brand, Model, Qty và Technical Notes.

#### G. Kiểm thử Responsive & Touch Scroll (Phase 9)
1. Mở Chrome/Firefox DevTools (F12) chuyển sang chế độ Device Mode (Mobile 375px/390px).
2. Kiểm tra thanh Category Quick-Access bar:
   - Hỗ trợ vuốt ngang cảm ứng (touch-scroll) mượt mà.
   - Không bị tràn màn hình (no horizontal scrollbar on body).
3. Bảng thông số kỹ thuật co giãn gọn gàng, chữ rõ ràng.

---

## 3. Hướng Dẫn Kiểm Thử Bằng Lệnh CLI / cURL

Mở Terminal và thực thi các lệnh sau:

### 3.1. Test HTTP Status & 301 Redirect
```bash
# 1. Kiểm tra Category route trả về HTTP 200 OK
curl -sS -I http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep "HTTP/1.1 200 OK"

# 2. Kiểm tra Shop route redirect 301 sang Catalog Category
curl -sS -I http://localhost:8080/shop/category/centrifugal-pumps | grep -E "(301 Moved Permanently|Location: /sre/catalog/category/centrifugal-pumps)"
```

### 3.2. Test Cô Lập Bộ Lọc 2 Tầng (2-Tier Filter Isolation)
```bash
# Toàn sàn (/sre/catalog): CÓ Global Filters (Industry/Application) nhưng KHÔNG CÓ Technical Specs
curl -sS http://localhost:8080/sre/catalog | grep -E "(sre-industry-filter|sre-application-filter)"
curl -sS http://localhost:8080/sre/catalog | grep "Technical specifications" || echo "PASS: Technical specs hidden on All Categories"

# Category Scope: CÓ đầy đủ Technical Specs và Dynamic Attributes
curl -sS http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep "Technical specifications"
curl -sS http://localhost:8080/sre/catalog/category/centrifugal-pumps | grep "Impeller Material"
```

### 3.3. Test Chi Tiết Sản Phẩm & Nhóm Thông Số Kỹ Thuật (Phase 5)
```bash
# Kiểm tra định danh Category & Product Type
curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -A 2 "<dt>Category</dt>"
curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep -A 1 "<dt>Product type</dt>"

# Kiểm tra phân nhóm Key vs Additional Specs
curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep "Key Specifications"
curl -sS http://localhost:8080/shop/sre-demo-p-001-demo-pump-001-demo-5 | grep "Additional Specifications"
```

---

## 4. Chạy Test Automation Hoàn Chỉnh (Phase 1 đến 9)

Chúng tôi đã chuẩn bị sẵn bộ script test tự động chạy độc lập và toàn diện 8 test suites:

```bash
# Chạy bộ test tự động kiểm tra toàn bộ 9 Phase (41 test cases)
./scripts/test_part2_automation.sh
```

Kết quả mong đợi: **Tất cả 41 test cases PASS (0 FAIL)**.
