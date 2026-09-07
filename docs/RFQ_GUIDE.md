# Customer RFQ cơ bản

Triển khai trong `mechanic_workshop`, Odoo 19 CE. Giữ nguyên `odoo_mechanic` / `mechanic_workshop`.

## Khách gửi yêu cầu

1. Mở http://localhost:8080/shop và chọn sản phẩm đã xuất bản.
2. Chọn variant và quantity, bấm **Add to RFQ**.
3. Trang `/rfq` cho sửa số lượng (**Update quantity**), **Remove**, **Continue browsing**.
4. Thêm nhiều hàng. Nhập Company, Contact name, Email; điền Phone, Project / Plant, Project location, Required delivery date, Additional requirements khi cần.
5. Bấm **Submit RFQ**, nhận mã `RFQ-xxxxxx`.

Quantity chỉ cập nhật khi bấm Update quantity. Danh sách lưu theo phiên trình duyệt và website, tối đa 100 sản phẩm. Sản phẩm không còn public/saleable sẽ bị loại khi mở lại danh sách. RFQ không xác nhận đơn bán hàng và không thu tiền.

## Nhân viên xử lý

1. Đăng nhập bằng tài khoản có quyền Sales, mở **Sales → Customer RFQs**.
2. Mở phiếu; kiểm tra thông tin khách và các dòng hàng. Liên kết **Lead** mở cơ hội CRM.
3. Chọn **Verified customer** từ Contacts sau khi xác nhận khách hàng. Nếu chưa có, nhân viên tạo contact bằng thao tác Odoo thông thường. Hệ thống không tự gán khách hàng hiện có bằng email khách tự nhập.
4. Bấm **Create / Open Quotation**. Báo giá native có đúng variant, quantity và UoM; giá lấy theo nghiệp vụ native. Nhân viên phải kiểm tra giá và điều kiện trước khi gửi.
5. Bấm lại mở cùng quotation. Không tự gửi email, xác nhận đơn, thanh toán hoặc giao hàng.

## Kiến trúc và quyền

- `sre.rfq` / `sre.rfq.line`: phiếu tiếp nhận riêng; các dòng liên kết `product.product` native.
- `crm.lead` và `sale.order`: liên kết ngược `sre_rfq_id`.
- Public/portal không có quyền ORM trên RFQ. Endpoint public chỉ tạo phiếu từ input đã kiểm tra; không có URL đọc phiếu bằng ID.
- Model có company rule. Website chỉ nhận sản phẩm public, saleable, active và đúng website/company.
- POST dùng CSRF; quantity hữu hạn, dương, giới hạn và phù hợp precision.
- Token theo phiên + unique constraint + transaction lock ngăn gửi lặp tạo phiếu trùng; khóa dòng khi tạo quotation ngăn hai lần bấm tạo hai báo giá.
- Không hiển thị giá, supplier hoặc cost trên RFQ website.

## Phạm vi còn lại

Chưa có attachments, dynamic technical fields theo Family/Application, country/industry/project stage/Incoterm, portal history, email thông báo tự động hoặc tìm sản phẩm chưa có SKU. Đây là RFQ foundation, không phải toàn bộ Technical RFQ Engine trong brief.

## Kiểm thử

```bash
docker compose -p odoo_mechanic exec -T odoo odoo -d mechanic_workshop \
  --config=/etc/odoo/odoo.conf -u mechanic_workshop --test-enable \
  --test-tags /mechanic_workshop --stop-after-init --http-port=8075
./scripts/agent_check.sh
```

Tests tạo dữ liệu trong transaction và rollback; không cần dùng dữ liệu khách thật. Sau đổi Python, restart service Odoo để worker nạp code mới. Website XML được nạp bằng module update.
