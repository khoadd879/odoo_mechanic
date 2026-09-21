# Project Rules

## 1. Git Commit Policy

> **QUY TẮC BẮT BUỘC (STRICT RULE):**
> **TUYỆT ĐỐI KHÔNG TỰ Ý COMMIT CODE (`git commit`).**

1. **Không tự động commit**: Sau khi hoàn thành code, sửa lỗi, chạy test hoặc cập nhật tài liệu, trợ lý AI **tuyệt đối không** tự ý chạy lệnh `git commit` hoặc `git commit -a`.
2. **Chỉ commit khi có yêu cầu**: Trợ lý AI chỉ được phép tạo commit khi người dùng có lệnh rõ ràng (ví dụ: *"commit đi"*, *"hãy commit code lại"*, *"commit giúp tôi"*).
3. **Quyền quản lý của người dùng**: Mọi thay đổi mã nguồn được giữ ở working directory / git staging để người dùng tự xem xét (`git diff`), kiểm tra và quyết định việc tạo commit hoặc hoàn tác.
