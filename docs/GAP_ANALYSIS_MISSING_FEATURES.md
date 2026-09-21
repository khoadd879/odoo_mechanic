# Báo cáo Phân tích Khoảng cách Tính năng (Gap Analysis) — Cập nhật
## Đối chiếu Hiện trạng Mã nguồn với SRE Commercial Website Transformation Brief

- **Dự án**: SRE Commercial Website (Odoo 19 / Mechanic Workshop)
- **Tài liệu tham chiếu**: `docs/SRE Commercial Website Transformation Brief.docx.md`
- **Thời điểm rà soát & cập nhật**: 15/09/2026
- **Trạng thái tổng quan**:
  - **Sprint 1 (Foundation)**: **100%** — Đã hoàn thành toàn bộ khung giao diện McMaster-Carr, tìm kiếm đa trường, giỏ RFQ, cờ duyệt giá công khai, upload ảnh tem mác và bản địa hóa 100% Tiếng Việt.
  - **Sprint 2 (Technical Commerce)**: **100%** — Đã hoàn thành bộ lọc dải số kỹ thuật (Áp suất, Nhiệt độ, Lưu lượng), Cross-Reference Engine (P0), Ma trận tương thích thiết bị (P0/P1), Attribute Profile, Document Governance & Thư viện CAD/PDF tập trung (P1).
  - **Sprint 3 (Discovery)**: **100%** — Đã hoàn thành Boiler Part Finder (P0) với Wizard 4 bước, Landing Pages / Danh bạ cho 10 Ngành & 10 Ứng dụng, Chuyên trang Unknown Part RFQ Wizard và BOM Multi-line Quick Paste (P1).
  - **Sprint 4 (B2B Platform)**: **100%** — Đã hoàn thành Customer Portal B2B (Lịch sử & Chi tiết RFQ, Re-order 1-click, Sổ tay thiết bị nhà máy My Plant, Bảng giá hợp đồng khung Contract Pricing, Tải trực tiếp CAD/PDF cho tài khoản đăng nhập, Upload BOM file Excel/CSV).

---

## I. Tổng quan Tiến độ theo 4 Sprint của Brief

| Sprint | Tên Sprint | Mục tiêu theo Brief | Tỷ lệ hoàn thành | Đánh giá hiện trạng |
| :--- | :--- | :--- | :---: | :--- |
| **Sprint 1** | **Foundation** | Navigation, Search, Category, Product Page, PIM/Odoo data model, RFQ Foundation, Pricing Policy | **100%** | Giao diện McMaster-Carr, tìm kiếm đa trường, giỏ RFQ, duyệt giá công khai (`public_price_approved`), upload ảnh tem mác và bản địa hóa song ngữ EN/VI hoàn tất. |
| **Sprint 2** | **Technical Commerce** | Dynamic RFQ, Technical Filters, Product Relationships, Cross Reference, Compatibility, Documents | **100%** | Đã có Bộ lọc dải số (Pressure, Temp, Flow), Cross-Reference Engine (`/cross-reference`), Ma trận tương thích (Tab 03/04), Document Governance & Thư viện CAD/PDF tập trung (`/technical-library`). |
| **Sprint 3** | **Discovery** | Boiler Part Finder, Industry Landing, Application Landing, Technical Library, SEO | **100%** | Đã hoàn thành Boiler Part Finder (Wizard 4 bước), 10 Landing Pages Ngành (`/sre/industry/*`), 10 Landing Pages Ứng dụng (`/sre/application/*`), Thư viện tài liệu kỹ thuật và Unknown Part RFQ / BOM Tool. |
| **Sprint 4** | **B2B Platform** | Customer Portal, Contract Pricing, RFQ History, Re-order, Saved Equipment, BOM Upload | **100%** | Đã hoàn thành Customer Portal B2B (`/my/rfqs`, `/my/plant`), Re-order 1-click, Contract Pricing, Tải trực tiếp CAD/PDF và upload BOM Excel/CSV (`/rfq/api/bom-upload`). |

---

## II. Các Tính năng ĐÃ HOÀN THÀNH (Chuyển từ Backlog sang Done)

1. **Boiler Part Finder (Mục 11 — P0)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Công cụ định danh phụ tùng lò hơi McMaster-Carr trực quan với Wizard 4 bước: Hãng lò hơi (*Miura, Cleaver-Brooks, Fulton, Hurst, Viessmann*) → Dòng / Model (*LX-200, CB-200, FB-A...*) kèm thông số Áp suất & Sản lượng hơi → Phân hệ (*Feedwater, Level, Burner, Blowdown, Safety, Steam*) → Danh sách linh kiện thay thế đã kiểm định kèm nhãn Critical Spare, thông số kỹ thuật và nút Add to RFQ 1-click.
   - Tuyến đường: `/boiler-finder`, `/sre/boiler-finder` và API JSON-RPC `/sre/boiler-finder/api/options`.
2. **Cross-Reference Engine & Tra cứu Mã chéo Đối thủ / OEM (Mục 12 — P0)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Cơ sở dữ liệu và công cụ tra cứu mã chéo từ thương hiệu đối thủ (*Spirax Sarco, TLV, Armstrong, Yoshitake, Grundfos, KSB...*) sang sản phẩm SRE phân phối.
   - Phân loại 3 cấp độ tương đương: **Direct Replacement (100% Fit & Function)**, **Drop-in Alternative**, **Obsolete Replacement**.
   - Tuyến đường: `/cross-reference`, `/sre/cross-reference` và API `/sre/cross-reference/api/search`.
3. **Ma trận Tương thích Thiết bị (Equipment Compatibility Matrix) (Mục 13 — P0/P1)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Tích hợp bảng danh sách máy móc tương thích vào **Tab 03 Compatibility** trên trang chi tiết sản phẩm (`/shop/*`), hiển thị Hãng, Model, Phân hệ, Vị trí lắp đặt và cờ Critical Spare.
   - Tích hợp bảng mã đối chiếu đối thủ/OEM vào **Tab 04 Cross reference & related products** trên trang chi tiết sản phẩm.
4. **Phê duyệt Hiển thị Giá Công khai (`public_price_approved`) (Mục 11)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Trường boolean `public_price_approved` trên `product.template`, tích hợp form backend, hiển thị giá công khai khi bật và nhãn an toàn `B2B Quote on Request` khi tắt.
5. **Upload Ảnh Tem Mác & Tài liệu vào Form RFQ (Mục 09 & 10)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Thêm `nameplate_image` và `nameplate_filename` trên `sre.rfq`, hỗ trợ upload ảnh/PDF qua form `/rfq`, tự động đính kèm vào cơ hội `crm.lead` và hiển thị xem trước trong backend.
6. **Bản địa hóa Toàn bộ Website sang Tiếng Việt (`vi_VN`)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Hoàn tất 100% từ điển dịch module (hơn 400 thuật ngữ), dịch toàn bộ Master Data (Pillars, Industries, Applications, Boiler Discovery, Cross References, Documents), chuyển đổi mượt mà giữa `/` và `/vi`.
7. **Landing Page Chuyên Biệt cho Industry & Application (Mục 14 & 15)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Tuyến đường và giao diện chuẩn cho 10 Ngành (`/sre/industry/<slug>`) và 10 Ứng dụng (`/sre/application/<slug>`), kèm 2 trang danh bạ tổng hợp (`/sre/industry` và `/sre/application`), liên kết trực tiếp từ trang chủ `#industries` và `#applications`.
8. **Bộ lọc Kỹ thuật Dạng Dải số (Numeric Range Slider & Inputs) (Mục 07)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Thêm 6 trường thông số định lượng (Áp suất bar, Nhiệt độ °C, Lưu lượng m³/h) trên `product.template`.
   - Widget sidebar kết hợp ô số [Min] - [Max] và dual-range slider với JS đồng bộ 2 chiều (`sre_catalog_filters.js`), lọc theo dải số thực, hiển thị active filter badges và hỗ trợ song ngữ.
9. **Document Governance & Thư viện CAD/PDF Tập trung (Mục 16 — P1)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Kế thừa `product.document` trong Odoo 19 CE, bổ sung phân quyền kiểm duyệt bản quyền:
     - **Public**: Cho phép tải trực tiếp không cần đăng nhập.
     - **Gated**: Hiển thị modal thu thập liên hệ (Họ tên, Email, Công ty, Yêu cầu kỹ thuật), tự động đồng bộ CRM Lead và trả link tải trực tiếp.
     - **Internal**: Chỉ lưu hành nội bộ kỹ sư SRE, ẩn hoàn toàn trên website và thư viện công khai.
   - Tự động nhận diện định dạng file CAD (STEP, DWG, DXF, IGES, PDF) từ đuôi file.
   - Kích hoạt Tab *02 Documents* trên trang chi tiết sản phẩm (`/shop/*`) với icon định dạng, dung lượng file, nút Tải ngay cho Public và modal thu thập liên hệ cho Gated.
   - Xây dựng Thư viện Kỹ thuật tập trung (`/technical-library` & `/sre/documents`) theo phong cách McMaster-Carr với bộ lọc Đa chiều (Loại tài liệu, Thương hiệu, Định dạng CAD) và tìm kiếm từ khóa.
10. **Chuyên trang "RFQ for Unknown Part" & BOM Multi-line Paste (Mục 09 & 10 — P1)**:
   - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
   - Xây dựng chuyên trang Định danh Phụ tùng Chưa rõ mã (`/rfq/unknown-part`) với Wizard 4 bước hướng dẫn trực quan: Hướng dẫn chụp tem mác → Nhập điều kiện vận hành (Môi chất, Áp suất bar, Nhiệt độ °C, Kiểu kết nối) → Thông tin liên hệ & Upload ảnh tem mác.
   - Tự động đồng bộ sang cơ hội `crm.lead` với độ ưu tiên cao nhất (3 sao / Khẩn cấp) và ghi nhận toàn bộ thông số vận hành vào Chatter.
    - Bổ sung công cụ Dán nhanh BOM đa dòng (*BOM Multi-line Quick Paste*) trên giỏ hàng `/rfq` cùng API JSON-RPC `/rfq/api/bom-parse` tự động phân tích và tra cứu chéo mã SKU, MPN và mã phụ tùng đối thủ/OEM vào giỏ RFQ.
11. **B2B Customer Portal, Saved Equipment & Platform Architecture (Mục 18 & 24 — Sprint 4)**:
    - Trạng thái: **ĐÃ HOÀN THÀNH (DONE)**.
    - Cổng thông tin khách hàng B2B tự phục vụ tích hợp sâu vào Odoo Portal:
      - **Lịch sử & Chi tiết RFQ (`/my/rfqs`, `/my/rfqs/<id>`)**: Xem danh sách phiếu yêu cầu báo giá, trạng thái xử lý (`submitted`, `quoted`), xem trước ảnh tem mác, thông số vận hành máy và liên kết trực tiếp tới báo giá chính thức (`sale.order`).
      - **Re-order Nhanh 1-Click (`/my/rfqs/reorder/<id>`, `/my/orders/reorder/<id>`)**: Tải toàn bộ danh mục linh kiện từ RFQ cũ hoặc Đơn hàng/Báo giá đã chốt vào giỏ RFQ hiện tại và chuyển hướng về `/rfq`.
      - **Sổ tay Thiết bị Nhà máy (My Plant / Saved Equipment) (`/my/plant`, `/my/plant/<id>`, `/my/plant/new`)**: Quản lý danh mục thiết bị nhà máy (`sre.customer.equipment`) theo mã tài sản (Plant Tag), vị trí lắp đặt, liên kết model lò hơi (`sre.boiler.model`). Tự động tra cứu phụ tùng tương thích đã kiểm nghiệm và cung cấp nút 1-click "Thêm tất cả phụ tùng vào RFQ" (`/my/plant/<id>/add-all-spares`).
      - **Bảng giá Hợp đồng Khung (B2B Contract Pricing)**: Khách hàng đăng nhập có bảng giá riêng sẽ thấy giá chiết khấu hợp đồng (`Contract: $ ...`) trên danh mục và chi tiết sản phẩm, trong khi khách vãng lai thấy `B2B Quote on Request`.
      - **Tải trực tiếp CAD/PDF cho Người dùng Đăng nhập**: Khách hàng B2B đăng nhập được bỏ qua form thu thập thông tin và tải ngay file CAD/PDF từ trang sản phẩm và thư viện kỹ thuật.
      - **Upload File BOM Excel/CSV (`/rfq/api/bom-upload`)**: Cho phép tải lên file `.xlsx`, `.xls`, `.csv` trực tiếp trên `/rfq`, tự động nhận diện cột và tra cứu mã SKU, MPN, Cross-reference.
      - **Bản địa hóa 100% Song ngữ**: Hỗ trợ đầy đủ tiếng Việt trên toàn bộ giao diện portal (`/vi/my/rfqs`, `/vi/my/plant`).

---

## III. Chi tiết Các Tính năng CÒN LẠI Cần Triển khai (Backlog)

*Hiện tại toàn bộ 4/4 Sprint theo SRE Commercial Website Transformation Brief đã hoàn thành 100%.* Không còn tính năng tồn đọng trong phạm vi đặc tả kỹ thuật ban đầu.

Các định hướng nâng cấp trong tương lai (Post-Launch Phase 2):
- Tích hợp thêm cổng thanh toán B2B nội địa (VNPay / VietQR) nếu mở bán hàng trực tiếp (khi chuyển từ mô hình Pure RFQ sang Hybrid B2B Checkout).
- Tích hợp hệ thống ERP bên ngoài (SAP, Oracle) thông qua webhook đồng bộ trạng thái đơn hàng.

---

## IV. Bảng Tổng hợp Danh mục (Status Matrix)

| STT | Tên tính năng | Phân loại | Độ ưu tiên | Trạng thái hiện tại | Sprint Brief |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 1 | **Boiler Part Finder (Wizard 4 bước)** | Discovery | **P0** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 3 |
| 2 | **Cross-Reference Engine (Mã thay thế/tương đương)** | Technical Commerce | **P0** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 2 |
| 3 | **Equipment Compatibility Matrix (Tab 03 Product Detail)** | Technical Commerce | **P0/P1** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 2 |
| 4 | **Document Governance (Quản lý quyền tài liệu & Thư viện CAD/PDF)** | Technical Library | **P1** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 2 |
| 5 | **Chuyên trang "RFQ for Unknown Part" & BOM Multi-line Paste** | RFQ Flow | **P1** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 3 |
| 6 | **Customer Portal B2B (RFQ History, Re-order, My Plant)** | B2B Platform | **P2** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 4 |
| 7 | **Contract Pricing (Bảng giá theo hợp đồng khung)** | B2B Platform | **P2** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 4 |
| 8 | **BOM Excel/CSV File Upload Parser** | B2B Platform | **P2** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 4 |
| 9 | **Direct CAD/PDF Download for Logged-in Users** | Technical Library | **P2** | **ĐÃ HOÀN THÀNH (DONE)** | Sprint 4 |

---

## V. Đánh giá & Khuyến nghị Tiếp theo

- **Toàn bộ 4 Sprint từ SRE Commercial Transformation Brief đã hoàn thành 100%**:
  - **Sprint 1 (Foundation)**: Giao diện McMaster-Carr, tìm kiếm đa trường (SKU, MPN, OEM, Hãng), giỏ RFQ, chính sách ẩn giá / duyệt giá công khai, upload ảnh tem mác.
  - **Sprint 2 (Technical Commerce)**: Bộ lọc dải số kỹ thuật (Áp suất, Nhiệt độ, Lưu lượng), Cross-Reference Engine, Ma trận tương thích máy móc (Tab 03/04), Document Governance & Thư viện CAD/PDF.
  - **Sprint 3 (Discovery)**: Boiler Part Finder (Wizard 4 bước), 10 Landing Pages Ngành & 10 Landing Pages Ứng dụng, Chuyên trang Unknown Part RFQ, BOM Multi-line Paste.
  - **Sprint 4 (B2B Platform)**: Customer Portal B2B (`/my/rfqs`, `/my/plant`), Re-order 1-click, Sổ tay thiết bị nhà máy My Plant, Bảng giá hợp đồng Contract Pricing, Direct CAD Download, và Upload BOM Excel/CSV.
  - Kiểm thử chất lượng tự động: `./scripts/agent_check.sh` đạt **30/30 PASS, 0 FAIL** (exit 0).
  - Bản địa hóa: 100% song ngữ Tiếng Anh / Tiếng Việt mượt mà trên toàn bộ nền tảng.
