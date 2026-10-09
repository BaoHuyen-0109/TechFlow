# Kiến trúc TechFlow

Giai đoạn 1 cung cấp Flask app factory, cấu hình, extensions, health check,
CLI kiểm tra database và Docker local. Giai đoạn 2 bổ sung 10 bảng nghiệp vụ,
migrations, seed và CLI Admin; xem [database](DATABASE.md). Chưa triển khai
đăng nhập, Dashboard hay CRUD.

```mermaid
flowchart LR
    Browser[Trình duyệt localhost:8000] --> Nginx[Nginx :80]
    Nginx --> Web[Flask + Gunicorn :8000]
    Web --> DB[MySQL 8.0 :3306]
    DB --> Volume[(mysql_data)]
```

- Chỉ Nginx publish trên loopback của host. MySQL không publish cổng.
- `backend` là network nội bộ giữa web và db; `frontend` nối Nginx và web.
- DB health check chạy SELECT 1 bằng user ứng dụng; web đợi DB healthy.
- `/health` chỉ là liveness của Flask, không xác nhận kết nối database.
  `flask --app wsgi check-db` kiểm tra kết nối MySQL thật, trả exit code 1 khi lỗi.
- Không tạo bảng, seed hoặc migration tự động lúc worker khởi động.
- Timestamp database thống nhất UTC; giao diện tương lai định dạng theo Asia/Ho_Chi_Minh.
- Chưa bật ProxyFix; không tin forwarded headers từ request để quyết định bảo mật.

## Ranh giới trách nhiệm

`routes.py`: nhận request, kiểm tra quyền khi có auth, trả response.
`forms.py`: validation backend bằng WTForms ở các giai đoạn sau.
`services/`: nghiệp vụ và transaction; không phụ thuộc vào template.
`models/`: ORM và quan hệ, sẽ được import đầy đủ để Alembic phát hiện.
`templates/`, `static/`: giao diện và assets.
`extensions.py`: extensions chưa bind; bind trong `create_app()`.

Các package auth/dashboard/categories/businesses/products/purchases/sales/users/audit
đã dành sẵn chỗ nhưng chưa đăng ký route. Nhóm phát triển nhập kho và bán hàng
phải đặt transaction, khóa hàng và chống xử lý lặp trong services, không đặt trong route.

## Định hướng UI đã thống nhất

Giai đoạn 3 dùng Bootstrap 5 và Jinja2, sidebar navy, content sáng, accent xanh dương,
CSS tùy chỉnh, icon thống nhất và offcanvas mobile. Assets Bootstrap lưu nội bộ.
Trang `/` hiện tại là trang thông tin nền tảng với CSS riêng; không phải layout quản trị cuối cùng.
Không tạo liên kết hoặc nút nghiệp vụ trước khi chức năng hoạt động.
