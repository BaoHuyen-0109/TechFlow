# Báo cáo Giai đoạn 3 — Authentication, Authorization & Admin Layout

Đây là báo cáo nghiệm thu ban đầu. Routing, layout và số bài test hiện tại được
cập nhật trong [báo cáo refactor Admin/Staff](STAGE_3_REFACTOR_REPORT.md).

Ngày kiểm tra: 09/10/2026. Phạm vi: chỉ giai đoạn 3 tại E:\AWS, tiếp tục Flask,
Flask-Login, Jinja2, Bootstrap 5, MySQL, Docker và kiến trúc theo đặc tả.

## Kết quả

Đăng nhập username hoặc email, kiểm tra hash mật khẩu, chặn inactive, đăng xuất
POST, CSRF, session và phân quyền backend đã hoạt động. Admin vào Dashboard và
trang phạm vi quản trị; Staff chỉ vào Dashboard giới hạn, `/admin` trả 403.
Dashboard hiển thị user/role thật, trạng thái module và empty state; không có KPI,
biểu đồ hoặc doanh thu giả. Chưa triển khai CRUD hay nghiệp vụ nhập/bán hàng.

Giao diện TechFlow tiếng Việt: Login riêng, sidebar navy với Bootstrap Icons,
topbar user/role/Logout, breadcrumb, flash dismissible, offcanvas tablet/mobile,
hover/focus, submit loading, toggle mật khẩu, reduced motion, trang lỗi chung
400/403/404/405/413/429/500/503. Assets Bootstrap 5.3.8 và Icons 1.13.1 lưu nội bộ
kèm license; không cần CDN khi mở website.

## Kiểm tra nền tảng và dữ liệu

Trước và sau cập nhật, db/web/nginx healthy; Docker Engine hoạt động. MySQL thật
kết nối thành công bằng check-db. Migration vẫn db55d828848e (head), db check trả
`No new upgrade operations detected`. Không có migration mới vì dùng bảng users
và audit_logs đã tồn tại. Không downgrade, không xóa/reset DB hoặc Docker volume.

| Dữ liệu demo | Trước cập nhật | Sau cập nhật |
| --- | ---: | ---: |
| users / Admin active | 0 / 0 | 0 / 0 |
| categories | 6 | 6 |
| businesses | 6 | 6 |
| products | 36 | 36 |
| purchase_receipts | 0 | 0 |
| sales_orders | 0 | 0 |
| stock_movements | 0 | 0 |
| audit_logs | 0 | 0 |

Đã đối chiếu cả id và marker của dòng stage1_probe id=367209152, giữ nguyên.
Không chạy lại seed trên demo trong giai đoạn này; kiểm thử seed lặp lại vẫn nằm
trong suite MySQL riêng. Không tạo tài khoản test trong database demo.

## Kết quả kiểm thử

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
```

**70 passed in 14.55s**, không skip. Bao gồm 45 bài giai đoạn 1–2 và 25 trường
hợp auth mới. Runner áp dụng db upgrade trước pytest trên techflow_test/MySQL
8.0.44 trong Docker, project/network/volume tách khỏi demo.

Phạm vi auth: username/email viết hoa, đúng/sai/không tồn tại, inactive, session
inactive bị thu hồi quyền ở request sau, đổi role có hiệu lực, Staff bị 403 và ẩn
menu, anonymous bị redirect, Logout GET bị 405/POST hoạt động, CSRF Login/Logout,
safe next cho URL ngoài/path bất thường, cookie/session trước login bị xóa, audit,
không echo/log password, form lỗi, session user id hỏng, giới hạn dùng chung
username/email, 6 lần sai đồng thời qua connection độc lập cho kết quả 5 thất bại
và 1 bị giới hạn. Các bài cấu hình production Secure, schema/constraints/quan hệ,
migration, hash/CLI, seed lặp lại và nền tảng vẫn đạt.

Kiểm tra bổ sung trên container chính: nginx -t thành công và reload cấu hình;
check-db thành công; db current/head và db check đạt. HTTP `/`, `/login`, `/health`
trả 200, `/dashboard` chưa login được chuyển tới Login. Kiểm tra POST không CSRF
qua Nginx test nhận 400, gửi liên tiếp vượt giới hạn nhận 429 có giao diện TechFlow
và thông báo tiếng Việt. Không dùng việc này để thử mật khẩu trên DB demo.

## Kiểm tra trình duyệt thực tế

Chạy scripts/verify_ui.py bằng Playwright Chromium 140 trên UI profile, cổng
8001, DB test riêng. Đã kiểm tra và xem ảnh ở cả ba kích thước:

| Viewport | Kết quả |
| --- | --- |
| Desktop 1440 × 1000 | Login, Dashboard, Admin, 404, Logout, redirect, không tràn ngang đạt |
| Tablet 834 × 1112 | Các luồng trên và mở/đóng sidebar offcanvas đạt |
| Mobile 390 × 844 | Các luồng trên và mở/đóng sidebar offcanvas đạt |
| Staff email login | Không thấy menu Admin; truy cập trực tiếp /admin trả 403 |

Không có JavaScript pageerror. Có thể xem trực tiếp các ảnh:

- [Login desktop](screenshots/stage3-login-desktop.png), [tablet](screenshots/stage3-login-tablet.png), [mobile](screenshots/stage3-login-mobile.png).
- [Dashboard desktop](screenshots/stage3-dashboard-desktop.png), [tablet](screenshots/stage3-dashboard-tablet.png), [mobile](screenshots/stage3-dashboard-mobile.png).
- [Menu tablet](screenshots/stage3-menu-tablet.png), [mobile](screenshots/stage3-menu-mobile.png).
- [Staff 403](screenshots/stage3-staff-403.png).

Đây là kiểm tra browser thật với viewport mô phỏng; chưa kiểm tra thiết bị cảm
ứng vật lý, Safari hoặc Firefox. Người dùng cần xác minh các môi trường đó nếu
buổi demo sử dụng. Công cụ browser tùy chọn, không thêm vào runtime image.

## Truy cập và tạo Admin

Services demo đang chạy tại **http://localhost:8000/login**. Hiện chưa có Admin;
không tự đặt mật khẩu. Tạo tài khoản bằng terminal tương tác:

```powershell
Set-Location E:\AWS
docker compose exec web flask --app wsgi create-admin --username admin --full-name "Quản trị TechFlow"
```

Nhập mật khẩu do bạn chọn hai lần tại prompt ẩn, 12–128 ký tự. Có thể thêm
`--email` nếu muốn login bằng email. Sau đó mở Login, nhập username/email và mật
khẩu vừa tạo; đăng nhập thành công chuyển về Dashboard. Không gửi mật khẩu vào
chat, không thêm vào command hoặc README. Nếu username đã tồn tại, CLI không
reset password; dùng tài khoản đã tạo hoặc chọn username khác.

## File mới

- `app/auth/forms.py`, `permissions.py`, `routes.py`.
- `app/services/auth_service.py`, `app/dashboard/routes.py`, `app/users/routes.py`.
- `app/templates/auth/login.html`, `layouts/admin.html`, `components/flash.html`,
  `dashboard/index.html`, `admin/index.html`.
- `app/static/css/techflow.css`, `app/static/js/app.js`.
- `app/static/vendor/bootstrap/` và `bootstrap-icons/`: CSS/JS/font/license.
- `tests/test_auth.py`, `scripts/verify_ui.py`, `requirements-ui.txt`.
- `.gitattributes`, `docs/AUTHENTICATION.md`, báo cáo này và 9 ảnh trong
  `docs/screenshots/`.

## File chỉnh sửa

- `app/__init__.py`: LoginManager, user loader, blueprint và security headers.
- `app/config.py`: session lifetime, ngưỡng đăng nhập sai.
- `app/errors.py`: lỗi bổ sung, rollback và fallback user khi lỗi 500.
- `app/templates/base.html`, `errors/error.html`, `main/index.html`: layout/assets
  và trạng thái giai đoạn hiện tại; giữ trang nền tảng `/` tương thích.
- `nginx/default.conf`: limiter POST /login và trang 429.
- `docker-compose.db-test.yml`: UI profile riêng dùng DB test.
- `.gitignore`, `.dockerignore`: bỏ qua browser cache.
- `README.md`, `docs/ARCHITECTURE.md`, `DECISIONS.md`, `GIT_WORKFLOW.md`, `SECURITY.md`.

Không sửa models, seed, CLI Admin hoặc migration đã áp dụng.

## Git và bàn giao

Khi bàn giao ban đầu, repository chưa có commit/remote. Trước thay đổi giai đoạn 3,
đã stage có chọn lọc snapshot 72 file giai đoạn 1–2. Sau khi người dùng yêu cầu
commit/push, đã tạo commit nền tảng `abb05e5` và tách thay đổi authentication/layout
thành commit tiếp theo. Đã kiểm tra index/working files không chứa giá trị secrets
trong .env; không sửa Git global. Chưa cấu hình remote, cần URL repository đích
để push. Hướng dẫn: [GIT_WORKFLOW.md](GIT_WORKFLOW.md).

`.env`, `.venv`, `.browser-cache` được git check-ignore xác nhận. Diff thay đổi
giai đoạn 3 không có lỗi whitespace. Snapshot giai đoạn 1–2 còn cảnh báo whitespace
vốn có ở đặc tả, header migration và dòng trống cuối DATABASE_SCHEMA.md; giữ nguyên
nội dung lịch sử và đặc tả, không coi `diff --cached --check` là đã đạt tuyệt đối.
Git có cảnh báo LF/CRLF trên một số file Windows, không phải lỗi chạy ứng dụng.

## Giới hạn và bước tiếp theo

Chưa có tài khoản Admin demo cho đến khi bạn tạo bằng CLI. Chưa có quản lý tài
khoản, reset mật khẩu, MFA hoặc kho phiên server; xem giới hạn session/proxy và
chống brute force trong [AUTHENTICATION.md](AUTHENTICATION.md), [SECURITY.md](SECURITY.md).
Không có lỗi chức năng còn ghi nhận trong phạm vi các bài kiểm tra đã chạy.

CRUD danh mục/nhà cung cấp/sản phẩm thuộc giai đoạn 4, KPI thuộc giai đoạn 6;
nhập kho, bán hàng và AWS chưa triển khai. Không tạo tài nguyên AWS hoặc phát sinh
chi phí dịch vụ cloud. Dừng ở giai đoạn 3 và chờ người dùng xác nhận tiếp theo.
