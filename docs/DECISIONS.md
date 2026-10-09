# Quyết định kỹ thuật

1. Dùng PyMySQL để tránh dependency biên dịch driver; Python 3.12 trong Docker.
2. URL.create xây URL database từ các biến thành phần, tránh lỗi ký tự đặc biệt
   trong password. DATABASE_URL là override tùy chọn; phải tự URL-encode credentials.
3. Không fallback secret hoặc database. Ứng dụng từ chối khởi động khi cấu hình thiếu.
4. Giai đoạn 1 dùng ba service để kiểm tra cùng đường đi Nginx → Gunicorn → MySQL.
   MySQL dùng utf8mb4/InnoDB mặc định, named volume, không publish cổng.
5. Giai đoạn 1 chưa có schema. Flask-Migrate được bind nhưng `db upgrade` chỉ có
   ý nghĩa sau khi bổ sung migrations ở giai đoạn 2.
6. Test nền tảng dùng Flask test client và mock kết nối để chạy độc lập, không
   tạo/xóa bảng. Đây không phải test tích hợp MySQL. `check-db` chạy thật là bước riêng.
7. Dành package cho module tương lai; không viết service nghiệp vụ giả hoặc route giả.
8. Chưa tạo cấu hình triển khai AWS/HTTPS production trong giai đoạn 1. Config Python
   có validation production nhưng Compose hiện tại chỉ dành cho local HTTP.
9. Dừng ở giai đoạn 1 chờ người dùng xác nhận; không tự chuyển sang models/migrations.

## Giai đoạn 2 (đã được xác nhận)

10. Tên danh mục unique theo utf8mb4_unicode_ci; product.business_id nullable.
11. FK RESTRICT ở DB và passive_deletes='all' ở ORM; không cascade xóa lịch sử.
12. Role/status dùng VARCHAR + CHECK để dễ mở rộng bằng migration có kiểm soát.
13. Giá và tổng dòng được CHECK tại MySQL; header totals và state transitions do
    service tương lai xử lý, không tự triển khai giao dịch trong giai đoạn 2.
14. Seed insert-only, tất cả stock=0; không tạo giao dịch, movement hay doanh thu giả.
    CLI Admin riêng, prompt ẩn, hash scrypt, không có tài khoản mặc định.
15. Bảo vệ stage1_probe và các bảng reflected ngoài metadata khi autogenerate.
16. Test integration bằng MySQL Docker riêng, không reset DB, không drop_all;
    giữ dữ liệu test có mã ngẫu nhiên trong volume test riêng.
17. Set session MySQL UTC và ẩn SQL parameters trong exception/log. Giữ stack tách
    routes/services/models/templates như giai đoạn 1. Dừng chờ duyệt trước giai đoạn 3.

## Giai đoạn 3 (đã được xác nhận)

18. Flask-Login + Flask-WTF; giữ schema/migration giai đoạn 2. AuditLog lưu các
    sự kiện auth và bộ đếm đăng nhập sai bằng HMAC, không lưu identity/password.
19. Dùng MySQL GET_LOCK trên connection riêng để giới hạn sai 5 lần/15 phút có
    hiệu lực giữa workers, kèm limiter POST theo IP ở Nginx. Không thêm Redis.
20. Admin/Staff kiểm tra ở backend; quyền user được tải lại ở mỗi request.
    `/admin` chỉ là trang thông tin phạm vi quyền, không triển khai quản lý user.
21. Bootstrap 5.3.8 và Bootstrap Icons 1.13.1 lưu nội bộ kèm license; CSP không
    unsafe-inline/unsafe-eval. Dashboard không có KPI khi chưa có truy vấn nghiệp vụ.
22. Browser verification dùng Playwright tùy chọn trên host và UI profile riêng
    nối DB test. Không tạo tài khoản hoặc mật khẩu demo mặc định.
23. Tách commit nền tảng/database giai đoạn 1–2 và commit auth/layout giai đoạn 3
    theo yêu cầu commit/push của người dùng. Push cần URL remote đích; không sửa
    Git global. Dừng trước giai đoạn 4.

## Refactor Giai đoạn 3 — hai không gian làm việc

24. Admin và Staff có Dashboard/layout/menu riêng; kế thừa workspace shell và
    navigation macro để tránh trùng auth, Logout, topbar và responsive.
25. Giữ alias `/dashboard` theo role và `/admin` chỉ Admin; đăng nhập về trang chủ
    role, next có allowlist chặt. Chính sách ban đầu chặn chéo hai Dashboard đã
    được thay bằng quyết định 28 bên dưới. Không đổi role trong database.
26. Admin ưu tiên thông tin tài khoản/ma trận quyền chỉ xem, trạng thái MySQL dùng
    SELECT 1 thật. Staff ưu tiên bố cục nghiệp vụ và shortcut không tương tác khi
    chưa triển khai, không dựng KPI, giao dịch hoặc cảnh báo giả.
27. Dùng CSS workspace riêng, sidebar 244/80px, scrollbar mảnh, offcanvas mobile;
    không đổi assets/framework. So sánh SHA-256 từng bảng trước/sau, kể cả users,
    audit_logs, stage1_probe và alembic_version. Không seed lại demo.

28. Theo điều chỉnh quyền của người dùng, Admin được cả Admin và Business;
    Staff chỉ Business. business_required dùng allowlist admin/staff, còn
    admin_required chỉ admin. Login mặc định giữ theo role. Menu chuyển workspace
    không đổi session/role và không yêu cầu login lại. Business vẫn dùng layout
    riêng; vai trò hiển thị lấy từ current_user, không suy ra từ layout.
