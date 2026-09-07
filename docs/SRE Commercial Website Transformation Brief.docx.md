# SRE COMMERCIAL WEBSITE

## ODOO WEBSITE TRANSFORMATION & IMPLEMENTATION BRIEF — V2

### 01\. MỤC TIÊU DỰ ÁN

Website Odoo hiện tại chỉ được xem là **template/staging base**.

Mục tiêu không phải là chỉnh sửa giao diện thời trang hiện tại thành một website công nghiệp đơn thuần.

Mục tiêu là chuyển đổi hệ thống thành:

**SRE Commercial — Digital Product Distribution Platform**

Nền tảng phục vụ hoạt động thương mại kỹ thuật B2B, tập trung vào:

* Industrial HVAC

* HVAC Building Systems

* Boiler Parts & Accessories

* Pumps

* Valves

* Heat Exchangers

* Instrumentation

* Controls & Automation

* Industrial Spare Parts

* Các nhóm Industrial MRO / Specialized Components trong tương lai

Website phải được thiết kế để có thể mở rộng từ vài trăm SKU lên hàng nghìn, chục nghìn và về lâu dài có thể quản lý quy mô 10,000–100,000+ SKU.

---

# 02\. TÀI LIỆU NGUỒN BẮT BUỘC

File:

**SRE\_COMMERCIAL\_WEBSITE\_PIM\_MASTER\_v2.xlsx**

là tài liệu Business/Data Master của hệ thống.

IT không được tự ý thay đổi:

* Product taxonomy

* Product family

* Attribute logic

* SKU logic

* Brand logic

* Cross-reference logic

* Compatibility logic

* Document governance

* RFQ logic

* Industry taxonomy

* Application taxonomy

nếu chưa có xác nhận từ SRE.

Odoo là **implementation/execution layer**.

PIM V2 là **commercial product data governance layer**.

---

# 03\. NGUYÊN TẮC KIẾN TRÚC

Không xây website theo logic:

Fashion → Category → Product → Add to Cart

Mà phải xây theo logic:

**Search → Technical Discovery → Product Qualification → RFQ → Sales → Procurement → Delivery → Repeat Order**

Website phải phục vụ ba nhóm khách hàng chính:

### A. Người biết chính xác sản phẩm cần mua

Ví dụ:

* OEM Part Number

* Manufacturer Part Number

* Model

* SKU

* Brand

* Product name

Họ phải tìm được sản phẩm nhanh.

### B. Người biết loại sản phẩm

Ví dụ:

* Boiler Water Level Probe

* Steam Trap

* Industrial Pump

* Control Valve

* Pressure Gauge

* Temperature Sensor

Họ phải có thể browse theo category và technical filters.

### C. Người chỉ biết vấn đề cần giải quyết

Ví dụ:

* Boiler water level control

* Pump replacement

* HVAC actuator replacement

* Steam leakage

* Boiler spare parts

* AHU control problem

Họ phải có thể tiếp cận sản phẩm thông qua Application / Problem / Industry.

---

# 04\. WEBSITE NAVIGATION

Không sử dụng:

**Industrial Equipment Supply**

làm navigation chính cho khách hàng.

Đây có thể là Odoo internal root category.

Navigation phía khách hàng nên theo business pillars:

1. HVAC & Building

2. Boiler & Thermal

3. Pumps

4. Valves

5. Heat Exchangers

6. Instrumentation

7. Controls & Automation

8. Industrial Spare Parts

Có thể bổ sung:

* Industries

* Applications

* Technical Library

* Request for Quotation

---

# 05\. GLOBAL SEARCH — P0

Search là chức năng cực kỳ quan trọng.

Search phải có khả năng tìm theo:

* Product Name

* SRE SKU

* Internal Reference

* Manufacturer Part Number

* OEM Part Number

* Model

* Brand

* Cross Reference

* Keyword

Ví dụ khách nhập:

**Danfoss 068-xxxx**

hoặc:

**Grundfos CR 10**

hoặc:

**water level probe**

hệ thống phải đưa ra kết quả phù hợp.

Exact Part Number phải được ưu tiên cao.

Không được chỉ search theo Product Name như website bán lẻ thông thường.

---

# 06\. CATEGORY PAGE — P0

Category page phải là **Technical Product Catalog**.

Không sử dụng layout kiểu:

* Fashion banner

* Product cards quá lớn

* Giá bán là thông tin chính

* Color/Size filter kiểu thời trang

Thay vào đó phải ưu tiên:

* Product name

* Brand

* Manufacturer Part Number

* Technical specifications

* Availability

* Lead Time

* RFQ

Có thể hỗ trợ:

**Grid View / List View / Technical Table View**

---

# 07\. TECHNICAL FILTERS

Filter phải được sinh từ:

**Product Family → Attribute Profile**

trong PIM V2.

Ví dụ:

### Valve

* Brand

* Valve Type

* Nominal Size

* Connection

* Pressure Class

* Material

* Actuation

* Control Signal

### Pump

* Brand

* Pump Type

* Flow

* Head

* Motor Power

* Connection

* Material

* Fluid/Application

### HVAC Instrument

* Brand

* Instrument Type

* Sensor Type

* Control Signal

* Measuring Range

* Connection

Không được tạo một bộ filter chung cho toàn website.

---

# 08\. PRODUCT PAGE — P0

Product page phải có cấu trúc kỹ thuật.

Thông tin ưu tiên:

### Product Identification

* Product Name

* Brand

* Manufacturer Part Number

* SRE SKU

* OEM Part Number / Cross Reference

### Technical Specification

Hiển thị dưới dạng technical table.

### Commercial Information

* Availability

* Lead Time

* MOQ nếu cần

* RFQ

Public price chỉ hiển thị đối với sản phẩm được SRE phê duyệt.

Không mặc định hiển thị giá.

### Documents

* Datasheet

* Installation Guide

* CAD

* Certificate

* Technical documents

Chỉ tài liệu đã qua Document Rights QA mới được public.

### Compatibility

Nếu đã được xác minh:

* Equipment Manufacturer

* Equipment Model

* Equipment Series

* Component / Position

### Cross Reference

Có thể hiển thị:

* Alternative

* Replacement

* Related

* Accessory

nhưng không được hiển thị thông tin nguồn cung/supplier nội bộ.

---

# 09\. RFQ — CORE FUNCTION

Website này là **RFQ-first B2B platform**, không phải retail e-commerce thuần túy.

Thay vì:

**Add to Cart**

phải ưu tiên:

**Add to RFQ**

Khách hàng có thể:

1. Chọn sản phẩm

2. Chọn quantity

3. Add to RFQ

4. Tiếp tục tìm sản phẩm khác

5. Submit RFQ

RFQ phải hỗ trợ nhiều sản phẩm trong một yêu cầu.

---

# 10\. TECHNICAL RFQ ENGINE

RFQ không nên là một form contact đơn giản.

Form phải có khả năng dynamic theo Product Family.

Thông tin cơ bản:

* Company

* Contact Person

* Email

* Phone

* Country

* Industry

* Project / Plant

* Project Location

* Project Stage

* Required Delivery Date

Thông tin sản phẩm:

* Part Number / SKU

* Manufacturer

* Model

* Quantity

* Unit

Thông tin kỹ thuật khi cần:

* Existing Equipment / OEM

* Equipment Model

* Application

* Fluid / Media

* Operating Pressure

* Operating Temperature

* Flow Rate

* Voltage

Commercial:

* Incoterm

* Urgency

* Replacement / New Installation

* Additional Requirements

Attachments:

* Photo

* Nameplate

* Existing Datasheet

* Drawing

* PDF/CAD nếu phù hợp

Không bắt khách hàng điền tất cả technical fields cho mọi sản phẩm.

**Field phải dynamic theo Product Family / Application.**

---

# 11\. BOILER PART FINDER — P0

Boiler Parts phải có một discovery engine riêng.

Logic:

**Boiler Manufacturer** ↓ **Boiler Type** ↓ **Boiler Model** ↓ **Component** ↓ **Part**

Ví dụ:

Manufacturer → Boiler Type → Model → Water Level Control → Water Level Probe / Electrode

Hoặc:

Manufacturer → Boiler Type → Model → Burner → Burner Nozzle

Mục tiêu:

Khách hàng không cần biết chính xác SKU vẫn có thể tìm được phụ tùng.

---

# 12\. CROSS REFERENCE ENGINE

PIM V2 có:

OEM → SRE SKU → Alternative → Replacement

Website phải hỗ trợ logic này.

Ví dụ:

OEM Part Number → SRE SKU → Compatible Alternative → Replacement

Nhưng:

**Không được public supplier/source intelligence.**

Khách hàng chỉ cần thấy thông tin cần thiết để mua đúng sản phẩm.

---

# 13\. COMPATIBILITY

Compatibility phải được quản lý riêng.

Logic:

**Product** → Equipment Type → Manufacturer → Model → Series → Component / Position → Application

Chỉ hiển thị compatibility đã được SRE xác minh/phê duyệt.

Không cho phép website tự suy luận rằng hai sản phẩm tương thích chỉ vì cùng category.

---

# 14\. INDUSTRY ARCHITECTURE

Industry là taxonomy độc lập với Product Category.

Các nhóm chính:

* Manufacturing

* Food & Beverage

* Textile

* Wood & Paper

* Chemical

* Steel & Metals

* Hotel & Resort

* Commercial Building

* Hospital

* School / University

Và có thể mở rộng:

* Oil & Gas

* Pharmaceutical

* Electronics / Semiconductor

* Data Center

* Infrastructure

Một sản phẩm có thể thuộc nhiều Industry.

Không duplicate product để phục vụ từng ngành.

---

# 15\. APPLICATION ARCHITECTURE

Application cũng là taxonomy độc lập.

Ví dụ:

* Boiler Water Level Control

* Boiler Burner & Combustion

* HVAC Control Components

* Industrial / HVAC Pumping

* Steam System Components

Một sản phẩm có thể phục vụ nhiều Applications.

Website phải cho phép:

Product → nhiều Applications

và:

Application → nhiều Products.

---

# 16\. DOCUMENT GOVERNANCE

Document Registry trong PIM V2 là nguồn quản trị.

Không được tự động copy toàn bộ catalogue/manual của OEM lên website.

Chỉ public tài liệu khi:

**Rights Verified \= Yes / Approved**

Các tài liệu chưa xác minh quyền sử dụng phải:

* Restricted

* Internal

* hoặc không public.

Đây là yêu cầu governance bắt buộc.

---

# 17\. BRAND

Brand chỉ là thông tin public.

Thông tin nội bộ như:

* Supply Status

* Preferred / Strategic

* Authorized Basis

* Supplier relationship

* Internal Commercial Control

* Source Verification

không được expose ra website.

Không được để khách hàng suy ra:

* SRE mua từ ai

* Giá vốn

* Supplier hierarchy

* Sourcing strategy

---

# 18\. CUSTOMER PORTAL — ARCHITECTURE READY

Giai đoạn đầu có thể chưa cần triển khai đầy đủ.

Tuy nhiên architecture phải cho phép phát triển:

* Customer-specific pricing

* Contract pricing

* RFQ history

* Quotation history

* Order history

* Re-order

* Saved products

* Saved RFQ

* Restricted technical documents

* Delivery/order status

Không thiết kế MVP theo cách khiến các chức năng này sau này phải rebuild toàn bộ.

---

# 19\. HOMEPAGE

Homepage phải chuyển hoàn toàn khỏi cảm giác fashion / retail.

Hero cần tập trung vào:

**Industrial HVAC, Boiler & Process Equipment**

và các nhóm:

**Components. Spare Parts. Controls. Instrumentation.**

Search bar phải là một thành phần rất lớn và nổi bật.

Ví dụ placeholder:

**Search by Part Number, Model, Brand or Product**

Sau đó:

### Quick Access

* HVAC

* Boiler Parts

* Pumps

* Valves

* Heat Exchangers

* Instrumentation

* Controls & Automation

* Industrial Spare Parts

Tiếp theo:

### Shop by Industry

### Shop by Application

### Featured Product Categories

### Technical Resources

### Request a Quote

---

# 20\. VISUAL DIRECTION

Không thiết kế theo:

* Fashion

* Consumer retail

* Marketplace giá rẻ

* Amazon clone

* Alibaba clone

Phong cách cần:

**Industrial / Technical / Premium / International / Engineering-driven**

Ưu tiên:

* Clean

* Structured

* Technical

* High information density nhưng không rối

* Professional B2B

* Mobile responsive

Website phải tạo cảm giác:

“Đây là một technical distributor mà kỹ sư, maintenance manager, procurement và FDI factory có thể tin tưởng.”

---

# 21\. ODOO DATA ARCHITECTURE

IT phải hiểu rõ:

**PIM V2 ≠ Odoo**

PIM V2:

Commercial Product Data Governance

Odoo:

ERP / Commerce / Operational Execution

Mapping phải theo:

PRODUCT\_MASTER → Odoo Product Template / Variant

PRODUCT\_FAMILY → Product Category / Custom Data

ATTRIBUTE\_PROFILES → Odoo Attributes / Values

CROSS\_REFERENCE → Product Relationship / Custom Model

COMPATIBILITY\_MATRIX → Compatibility Model / Relation

DOCUMENT\_REGISTRY → Product Documents / Attachments

INDUSTRY\_MASTER → Website Taxonomy

APPLICATION\_MASTER → Website Taxonomy

TECHNICAL\_RFQ\_FIELDS → RFQ Custom / Dynamic Fields

PRODUCT\_RELATIONSHIPS → Alternative / Replacement / Accessory / Related

---

# 22\. KHÔNG ĐƯỢC LÀM

IT không được:

1. Chỉ đổi màu và banner của template hiện tại.

2. Giữ nguyên logic Fashion.

3. Dùng Add to Cart làm CTA chính cho toàn bộ sản phẩm.

4. Dùng price làm thông tin trung tâm.

5. Tạo filter chung cho tất cả categories.

6. Hard-code technical attributes vào frontend.

7. Hard-code category structure vào code.

8. Duplicate product chỉ vì khác Industry/Application.

9. Public supplier/source information.

10. Public document chưa qua rights verification.

11. Tạo hàng nghìn variant không cần thiết chỉ vì attribute.

12. Xây database khiến sau này không thể mở rộng 10k–100k SKU.

13. Để Odoo default architecture quyết định business taxonomy.

---

# 23\. ACCEPTANCE CRITERIA — MVP

Trước khi nghiệm thu, IT phải chứng minh được:

### Search

Có thể search:

SKU / MPN / OEM PN / Model / Brand / Keyword.

### Category

Có technical filters khác nhau theo Product Family.

### Product

Có:

Product → Technical Specification → Documents → Compatibility → Related Products → RFQ.

### RFQ

Có thể:

Add multiple products → quantity → technical information → attachment → submit RFQ.

### Boiler

Có Boiler Part Finder.

### Cross Reference

Có OEM PN → SRE SKU → Alternative / Replacement.

### Industry

Có Industry landing pages và product mapping.

### Application

Có Application landing pages và product mapping.

### Governance

Public/private data được phân tách.

### Scalability

Kiến trúc không phụ thuộc vào vài chục sản phẩm demo hiện tại.

---

# 24\. PHƯƠNG PHÁP TRIỂN KHAI

Không build toàn bộ website một lần.

Đề nghị triển khai theo 4 sprint:

### SPRINT 1 — FOUNDATION

* Navigation

* Search

* Category

* Product page

* PIM/Odoo data model

* RFQ foundation

### SPRINT 2 — TECHNICAL COMMERCE

* Technical filters

* Dynamic RFQ

* Product relationships

* Cross Reference

* Compatibility

* Documents

### SPRINT 3 — DISCOVERY

* Boiler Part Finder

* Industry

* Application

* Technical Library

* SEO landing architecture

### SPRINT 4 — B2B PLATFORM

* Customer Portal

* Contract Pricing

* RFQ history

* Re-order

* Saved products

* Customer-specific documents

* Advanced procurement/inventory integration

---

# 25\. NGUYÊN TẮC CUỐI CÙNG

Đây không phải dự án:

“Làm một website đẹp hơn.”

Đây là dự án:

**Chuyển Odoo staging website thành Digital Product Distribution Platform của SRE Commercial.**

Website phải được xây từ:

**SRE Business Model** → **Commercial Product Taxonomy** → **PIM V2** → **Odoo Data Model** → **Website UX/UI** → **RFQ / CRM** → **Inventory / Procurement** → **Customer Portal**

PIM V2 là cơ sở dữ liệu quản trị sản phẩm.

Odoo là nền tảng vận hành.

Website là giao diện bán hàng và technical discovery.

Mục tiêu cuối cùng:

**Search → Find → Verify → RFQ → Quote → Order → Deliver → Re-order**

và kiến trúc phải đủ khả năng mở rộng thành một **industrial technical distribution platform**, không phải một website bán hàng đơn thuần.