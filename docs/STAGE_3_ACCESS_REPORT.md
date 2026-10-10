# Giai đoạn 3 — Admin truy cập cả hai không gian

Ngày kiểm tra: 09/10/2026. Điều chỉnh quyền trên bản refactor hiện có, không
triển khai nghiệp vụ giai đoạn 4 trở đi. Các thay đổi chưa commit từ lần refactor
trước được giữ nguyên; không reset, ghi đè hoặc force-push.

## Chính sách hiện tại

| Chức năng | Admin | Staff |
| --- | --- | --- |
| /admin/dashboard, /admin | Được truy cập | 403 |
| /staff/dashboard | Được truy cập | Được truy cập |
| Trang mặc định sau login và /dashboard | Admin Dashboard | Business Dashboard |
| Không gian kinh doanh trong sidebar Admin | Có | Không có sidebar Admin |
| Quay về quản trị trong Business topbar | Có | Không hiển thị |

admin_required dùng role_required('admin'); business_required dùng
role_required('admin', 'staff'). Cả hai bao gồm Flask-Login login_required.
Backend chặn role ngoài allowlist. Bảng quyền trên Dashboard Admin đã sửa Admin
được truy cập Business. Không chỉ dùng việc hiện/ẩn menu làm phân quyền.

Giữ riêng layout/sidebar Admin và Business. Business giữ bố cục, cards, empty
states của bản trước; chỉ thêm liên kết trở về quản trị cho Admin và hiển thị role
thực. Brand/breadcrumb của Admin trong Business trỏ đúng trang chủ Business.
Trên mobile, liên kết trở về quản trị hiển thị icon với aria-label và title; không
làm tràn topbar. Không thêm CRUD, KPI hoặc dữ liệu giả.

## Phiên đăng nhập và bảo mật

Chuyển workspace là điều hướng GET, không logout/login, không thay đổi role trong
database, không thay user_id hoặc CSRF/session identifier. Login mặc định vẫn về
Dashboard của vai trò; allowlist chống open redirect không nới lỏng. Giữ nguyên
password hashing, cookie/session security, CSRF, rate limiting và audit logging.
GET chuyển workspace không tạo login audit mới.

## Kiểm thử

`docker compose -f docker-compose.db-test.yml run --build --rm tests`:
**85 passed in 14.79s**, không skip. Bao gồm toàn bộ 76 bài hồi quy trước và 9 bài
mới: 8 unit cases cho decorator/anonymous/role lạ, 1 MySQL integration case kiểm
tra Admin đi qua hai Dashboard, giữ nguyên phiên/CSRF/role và số audit.
Các bài role/route cũ đã cập nhật theo ma trận mới, Staff vẫn bị 403 khi sửa URL.

Playwright Chromium kiểm tra Admin/Staff trên desktop 1440×1000, tablet 834×1112,
mobile 390×844: cả 6 luồng đạt. Admin click menu Không gian kinh doanh, vào đúng
layout Business với role Quản trị viên, click Quay về quản trị về đúng layout Admin.
Chỉ có một POST login trong toàn bộ luồng chuyển qua lại. Staff không thấy link
quản trị, truy cập trực tiếp /admin và /admin/dashboard đều 403. Giữ kiểm tra
collapse/offcanvas, hover/focus bằng bàn phím, active menu, Logout, CSRF flow,
404, anonymous redirect, không tràn ngang, không pageerror/asset error.

Ảnh cũ đã được dọn theo yêu cầu giảm screenshot. Xem [4 ảnh minh chứng hiện tại](screenshots/README.md); ảnh đã commit trước đây vẫn có trong lịch sử Git.

Chromium là trình duyệt thật với viewport mô phỏng, chưa kiểm tra thiết bị vật lý,
Safari/Firefox hoặc screen reader.

## Bảo toàn dữ liệu

Fingerprint chỉ đọc trước/sau trên cả 12 bảng khớp hoàn toàn: users 1, audit_logs 4,
categories 6, businesses 6, products 36, stage1_probe 1, alembic_version 1; các
bảng giao dịch/movement vẫn rỗng. Giữ Admin/mật khẩu/role, không seed lại demo,
không sửa migration hoặc xóa volume. Snapshot mới nằm trong thư mục ignore:

```powershell
.\.venv\Scripts\python.exe scripts/verify_demo_integrity.py compare --snapshot-file .docker-local/admin-business-access-before.json
```

Snapshot cũ của đợt refactor được giữ riêng. Lần điều chỉnh này dùng snapshot mới
vì audit demo đã có thêm hoạt động hợp lệ của người dùng trước khi bắt đầu.
Migration vẫn db55d828848e (head), db check không có thay đổi. Demo web/db/nginx
healthy sau cập nhật; môi trường test dừng riêng và giữ volumes.

## Các file thay đổi trong lần điều chỉnh quyền

- app/auth/permissions.py: decorator nhiều role và business_required.
- app/dashboard/routes.py: kiểm tra quyền Business và home theo workspace.
- app/templates/layouts/admin.html: liên kết Không gian kinh doanh.
- app/templates/layouts/staff.html: liên kết Quay về quản trị có điều kiện.
- app/templates/layouts/workspace.html: slot chuyển workspace và home riêng.
- app/templates/admin/dashboard.html: ma trận quyền đúng.
- app/templates/staff/dashboard.html: nhãn phiên theo role thật.
- app/templates/errors/error.html: chọn layout Business đúng ngữ cảnh.
- app/static/css/workspace.css: style liên kết chuyển workspace responsive.
- tests/test_auth.py; mới tests/test_permissions.py: integration/unit checks.
- scripts/verify_ui.py: chuyển qua lại và Staff bị chặn; ảnh access-*.png.
- scripts/verify_demo_integrity.py: hỗ trợ snapshot-file để không ghi đè baseline cũ.
- README.md, docs/ARCHITECTURE.md, AUTHENTICATION.md, SECURITY.md, DECISIONS.md,
  STAGE_3_REFACTOR_REPORT.md và báo cáo này.

Chưa commit/push lần điều chỉnh. Không ghi nhận lỗi trong phạm vi đã kiểm thử.
Chưa có quản lý user, đăng ký, CRUD, nhập/bán hàng, báo cáo/KPI hoặc AWS. Dừng tại
giai đoạn 3, chờ người dùng xác nhận tiếp theo.
