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
