# TechFlow — Báo cáo Giai đoạn 3: Authentication, Authorization và hai workspace

Báo cáo tổng hợp các đợt đăng nhập/layout, refactor Admin–Business và điều chỉnh
quyền ngày 09/10/2026. Các số kiểm thử dưới đây thuộc từng lần nghiệm thu đã
thực hiện, không phải lượt chạy mới khi gộp tài liệu.

<a id="hai-workspace"></a>
## Kết quả và phân quyền

- Đăng nhập username hoặc email, kiểm tra password hash, chặn inactive và thu hồi
  phiên khi tài khoản bị khóa/đổi role. Đăng xuất bằng POST có CSRF.
- Flask-Login, session, cookie HttpOnly/SameSite/Secure theo environment, safe
  redirect, rate limiting MySQL/Nginx và audit logging hoạt động.
- Hai Dashboard có layout/sidebar riêng; dùng chung workspace shell, navigation
  macro, topbar, breadcrumb, flash và design tokens.
- Admin mặc định vào Admin Dashboard, chuyển sang Business rồi quay về quản trị
  bằng GET, giữ nguyên user/role/CSRF/session và không tạo login audit mới.
- Staff chỉ vào Business; quyền được kiểm tra ở backend, không chỉ ẩn menu.

<a id="phan-quyen"></a>

| Đường dẫn/chức năng | Admin | Staff |
| --- | --- | --- |
| `/admin/dashboard`, alias `/admin` | Được truy cập | 403 |
| `/staff/dashboard` | Được truy cập | Được truy cập |
| `/dashboard` và mặc định sau login | Admin Dashboard | Business Dashboard |
| Không gian kinh doanh trong sidebar Admin | Có | Không có sidebar Admin |
| Quay về quản trị trong Business | Có | Không hiển thị |
| `POST /logout` | Có CSRF | Có CSRF |

`admin_required` dùng `role_required('admin')`; `business_required` dùng
`role_required('admin', 'staff')`, cùng dựa trên Flask-Login. Quy tắc refactor
ban đầu chặn Admin vào Business đã được thay thế hoàn toàn bằng bảng trên.

## Giao diện và bảo mật

Login tiếng Việt, sidebar navy/xanh dương, Bootstrap Icons, vùng nội dung sáng;
thu gọn desktop 244→80px, offcanvas tablet/mobile, active/hover/focus, bàn phím,
reduced motion, password toggle và submit loading. Không lưu dữ liệu nhạy cảm
hoặc tùy chọn collapse vào localStorage.

Assets Bootstrap 5.3.8 và Icons 1.13.1 lưu nội bộ kèm license. Trang lỗi đồng bộ
400/403/404/405/413/429/500/503. Dashboard giai đoạn này hiển thị tài khoản/role
thật, trạng thái MySQL qua SELECT 1 và nội dung chưa triển khai; không giả KPI,
Docker/AWS monitoring hoặc dựng nút quản lý tài khoản chưa có backend.

## Kiểm thử đã nghiệm thu

| Đợt | Backend MySQL 8.0.44 riêng | Browser |
| --- | --- | --- |
| Authentication/layout ban đầu | 70 passed / 14.55s: 45 bài nền tảng/database + 25 auth | Login, Dashboard, lỗi, logout và responsive đạt |
| Refactor hai workspace | 76 passed / 13.63s: thêm 6 ca | 6 tổ hợp Admin/Staff × desktop/tablet/mobile đạt |
| Admin truy cập cả hai workspace | 85 passed / 14.79s: thêm 8 unit + 1 integration | 6 tổ hợp, chuyển qua lại chỉ một POST login, Staff403 đạt |

Phạm vi: đúng/sai/username/email/inactive, role thay đổi, anonymous, Logout
GET405/POST, CSRF, next URL ngoài/path bất thường, session ID hỏng, cookie trước
login, audit và không echo/log password. Sáu lần sai đồng thời qua connection
độc lập cho 5 thất bại + 1 bị giới hạn. POST thiếu CSRF qua Nginx test nhận400,
vượt limiter nhận429; giữ cấu hình production Secure và toàn bộ kiểm thử cũ.

Browser Chromium: 1440×1000, 834×1112, 390×844; collapse/offcanvas, menu/anchor
thật, bàn phím/hover, 404, loading, không tràn ngang/pageerror/asset error.
Chưa kiểm thử thiết bị vật lý, Safari/Firefox hoặc screen reader.

## Bảo toàn dữ liệu

Không migration mới; revision tại Giai đoạn 3 là `db55d828848e (head)`,
db check không có upgrade operations. Không sửa models, seed, CLI Admin hoặc
migration đã áp dụng; không reset database/xóa volume/đổi mật khẩu.

Fingerprint/count 12 bảng khớp ở mỗi đợt. Baseline thay đổi giữa các lần do hoạt
động hợp lệ có sẵn: ban đầu users/audit là0/0; refactor1/2; điều chỉnh quyền1/4.
Categories6, businesses6, products36 và stage1_probe1 giữ nguyên; giao dịch/
movement rỗng. Snapshot chỉ đọc nằm trong `.docker-local`, không đưa vào Git.
Test account chỉ ở database test, không dùng tài khoản demo để thử brute force.

## File triển khai

| Nhóm | File tạo/chỉnh sửa chính |
| --- | --- |
| Auth/quyền/routes | app/auth/{forms,permissions,routes}.py; app/services/auth_service.py; app/dashboard/routes.py; app/users/routes.py |
| Nền tảng | app/{__init__,config,errors}.py; app/services/workspace_service.py |
| Layout và trang | app/templates/auth/login.html; layouts/{workspace,admin,staff}.html; components/{navigation,flash}.html; admin/dashboard.html; staff/dashboard.html; base.html; main/index.html; errors/error.html |
| Assets | app/static/css/{techflow,workspace}.css; app/static/js/app.js; app/static/vendor/{bootstrap,bootstrap-icons}/ |
| Kiểm thử | tests/{test_auth,test_permissions}.py; scripts/{verify_ui,verify_demo_integrity}.py; requirements-ui.txt |
| Cấu hình/tài liệu | nginx/default.conf; docker-compose.db-test.yml; .gitattributes; .gitignore; .dockerignore; README; ARCHITECTURE, AUTHENTICATION, DECISIONS, GIT_WORKFLOW, SECURITY |

Hai template cũ `admin/index.html`, `dashboard/index.html` được thay thế; route
cũ giữ alias có kiểm tra quyền. Không thêm dependency runtime trong đợt refactor.

## Git, truy cập và giới hạn

Các checkpoint: nền tảng/database `abb05e5`, auth ban đầu `14f0a52`, bản hoàn
thiện authentication/hai Dashboard `09e9c4ba4f9bdefa7fbd6516e0f2911da79bd8b7`
(`feat: complete authentication and role-based dashboards`). Bản hoàn thiện
được push main thông thường theo xác nhận; không force/reset lịch sử chung.

Mở http://localhost:8000/login bằng tài khoản đã cấp. CLI tạo Admin khi chưa có
tài khoản, yêu cầu nhập mật khẩu tại prompt ẩn, không đặt mặc định:

```powershell
docker compose exec web flask --app wsgi create-admin --username admin --full-name "Quản trị TechFlow"
```

CLI không reset mật khẩu tài khoản trùng username. Không ghi mật khẩu vào chat,
command hoặc tài liệu. Giới hạn quản lý tài khoản/reset mật khẩu/MFA/kho phiên
và proxy xem [AUTHENTICATION.md](AUTHENTICATION.md), [SECURITY.md](SECURITY.md).
Không ghi nhận lỗi còn tái hiện tại nghiệm thu Giai đoạn 3.

CRUD, giao dịch, khách hàng, bảo hành và KPI được phát triển ở các giai đoạn sau;
xem [Giai đoạn 4](STAGE_4_REPORT.md), [Giai đoạn 5](STAGE_5_REPORT.md),
[Giai đoạn 6](STAGE_6_REPORT.md). [Danh mục ảnh còn giữ](screenshots/README.md);
ảnh lịch sử đã dọn vẫn có trong Git, không tạo thêm ảnh khi gộp tài liệu.
