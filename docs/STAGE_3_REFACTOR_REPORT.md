# Refactor Giai đoạn 3 — Admin và Staff Dashboard

Đây là báo cáo lần refactor ban đầu. Chính sách chặn Admin vào Business trong
báo cáo này đã được thay thế: **Admin được cả hai không gian, Staff chỉ Business**.
Xem [báo cáo điều chỉnh quyền hiện tại](STAGE_3_ACCESS_REPORT.md).

Ngày nghiệm thu: 09/10/2026. Chỉ hoàn thiện authentication, authorization và UI/UX
giai đoạn 3; giữ Flask, Jinja2, Bootstrap 5, MySQL, Docker, Nginx và assets nội bộ.
Không triển khai giai đoạn 4, nhập/bán hàng, AWS hoặc thêm dịch vụ cloud.

## Kiến trúc và hành vi

Hai không gian có trang chủ, nội dung và menu riêng. Admin tập trung vào tài
khoản/quyền/trạng thái, Staff tập trung vào công việc kinh doanh. Dùng chung
workspace shell, macro navigation, design tokens, topbar, breadcrumb, flash và
POST Logout, không sao chép Dashboard Admin rồi ẩn bớt nội dung.

| Đường dẫn | Hành vi hiện tại |
| --- | --- |
| /login | Chung; Admin login về /admin/dashboard, Staff về /staff/dashboard |
| /dashboard | Alias có xác thực, redirect theo role |
| /admin | Alias chỉ Admin; redirect /admin/dashboard, Staff bị 403 |
| /admin/dashboard | Chỉ Admin active |
| /staff/dashboard | Chỉ Staff active |
| POST /logout | Cả hai vai trò, phải có CSRF |

Hai Dashboard hiện chặn truy cập chéo ở backend bằng admin_required và
staff_required, cùng dựa trên role_required/login_required. Đây là ranh giới
workspace, không thay đổi role trong DB hoặc định nghĩa lại quyền Admin đối với
các module nghiệp vụ sẽ phát triển theo đặc tả. Nếu sau này cho Admin xem không
gian kinh doanh thì cần mở chính sách rõ ràng và bổ sung tests.

next vẫn được lọc bằng allowlist đường dẫn chính xác. Trong phạm vi chỉ có hai
trang chủ, mọi next sau login được quy về Dashboard của vai trò vừa xác thực;
URL ngoài/path bất thường và đường dẫn role khác không dẫn người dùng ra ngoài
hoặc vượt quyền. Trang lỗi authenticated chọn layout của chính tài khoản.

## Giao diện đã hoạt động

Admin: sidebar gọn 244px, không có danh sách kinh doanh và banner lớn. Menu dẫn
tới Dashboard và các section thật: tài khoản, ma trận quyền chỉ đọc, trạng thái
hệ thống. Thông tin user lấy từ MySQL; trạng thái kết nối chạy SELECT 1 thật tại
lần tải trang. Trạng thái ứng dụng là phản hồi request hiện tại. Không tuyên bố
đang giám sát Docker/AWS, không tạo tổng số user/audit giả. Quản lý user, sửa vai
trò, audit viewer và cấu hình chưa có backend nên không dựng nút hoặc trang giả.

Staff: layout/menu kinh doanh riêng, header theo tài khoản thật và ngày Việt Nam
từ clock hệ thống. Có vùng tổng quan hoạt động, bốn shortcut, hoạt động gần đây,
thông báo và thông tin phiên. Những vùng chưa có nghiệp vụ dùng trạng thái
"Chưa triển khai"; không đưa số 0, doanh thu, biểu đồ, giao dịch hoặc cảnh báo giả.
Shortcut và menu chưa khả dụng là nội dung không tương tác, không phải nút có
handler giả. Menu không có quản trị hệ thống.

UI chung: navy/xanh dương/nền sáng, typography tiếng Việt, card/spacing thống nhất,
sidebar có scrollbar mảnh và phần nav cuộn độc lập, thu gọn desktop từ 244 xuống
80px bằng nút hoạt động thật, offcanvas tablet/mobile. Semantic nav/main/section,
aria-current, aria-disabled, aria-label, keyboard focus, hover và reduced motion
được giữ. Không lưu tùy chọn collapse hoặc dữ liệu nhạy cảm vào localStorage.
Login, password toggle, submit loading, flash và Logout giữ hoạt động.

## Bảo toàn dữ liệu và bảo mật

Trước khi sửa, Git sạch trên main, HEAD 14f0a52 trùng origin/main tại
https://github.com/BaoHuyen-0109/TechFlow.git. Docker db/web/nginx healthy;
check migration ở head db55d828848e, db check không phát hiện thay đổi schema.

Đã snapshot chỉ đọc bằng scripts/verify_demo_integrity.py: COUNT và SHA-256 toàn
bộ giá trị mỗi bảng, gồm cả password_hash của users trong fingerprint nhưng không
in/lưu plaintext hoặc hash mật khẩu riêng. Snapshot nằm trong .docker-local đã
ignore. Sau cập nhật và kiểm thử, **cả 12 bảng có số dòng và fingerprint giống
hệt trước khi sửa**, gồm:

| Bảng demo | Số dòng giữ nguyên |
| --- | ---: |
| users | 1 |
| audit_logs | 2 |
| categories | 6 |
| businesses | 6 |
| products | 36 |
| purchase_receipts / purchase_receipt_items | 0 / 0 |
| sales_orders / sales_order_items | 0 / 0 |
| stock_movements | 0 |
| stage1_probe | 1 |
| alembic_version | 1 |

Không tạo account hoặc sửa password/role trên demo, không seed lại, không sửa
migration đã áp dụng, không reset DB, không xóa volume. Account Admin hiện tại
được giữ nguyên. Flask-Login, scrypt hashing, strong session, CSRF, HttpOnly/
SameSite/Secure theo environment, rate limiter MySQL/Nginx, audit, security headers
và xử lý lỗi giữ nguyên. Fingerprint bao gồm audit hiện có; các login kiểm thử
chỉ thực hiện ở database test.

## Kiểm thử

Lệnh đầy đủ:

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
docker compose -f docker-compose.db-test.yml --profile ui up -d --wait ui-nginx
docker compose -f docker-compose.db-test.yml exec -T ui-nginx nginx -s reload
.\.venv\Scripts\python.exe scripts/verify_ui.py
.\.venv\Scripts\python.exe scripts/verify_demo_integrity.py compare
```

**76 passed in 13.63s** trên MySQL 8.0.44 Docker test riêng, không skip. Giữ đủ
phạm vi 70 bài giai đoạn 1–3, cập nhật các expectation route/heading cũ theo hành
vi mới; không xóa bài test hoặc tắt CSRF/authorization để vượt qua test. Thêm 6
trường hợp: anonymous ở hai route mới, phân tách workspace cho cả hai role,
Admin thấy trạng thái DB lỗi, và service xử lý lỗi connection an toàn.

Đã kiểm tra login đúng/sai/username/email/inactive; session bị vô hiệu khi khóa
account/đổi role; Logout/CSRF; safe redirect; route alias; forbidden chéo role;
layout đúng vai trò ở 403/404; hash/CLI/seed/schema/constraints/migrations cũ;
giới hạn username/email dùng chung và thử đồng thời giữa connection độc lập.

Playwright Chromium chạy sáu luồng (Admin và Staff × desktop 1440×1000, tablet
834×1112, mobile 390×844). Tất cả đạt: login theo role, topbar, active menu,
thu gọn/mở rộng desktop, offcanvas mobile, hover, focus bằng Shift+Tab/Tab,
link/anchor thật, menu/shortcut khóa không có link/button, redirect cũ, forbidden,
404, Logout, anonymous redirect, không tràn ngang, không JavaScript pageerror và
không lỗi tải assets. Account ngẫu nhiên chỉ tạo trong techflow_test.

Đã chụp 21 ảnh mới và tự xem lại cả hai Dashboard trên ba viewport. Sau kiểm tra
trực quan đã chỉnh phần phiên Staff mobile và bảng quyền Admin mobile để nội dung
không bị ép hẹp/cắt. Ảnh chính:

| Vai trò | Desktop | Tablet | Mobile |
| --- | --- | --- | --- |
| Admin | [Ảnh](screenshots/refactor-admin-desktop.png) | [Ảnh](screenshots/refactor-admin-tablet.png) | [Ảnh](screenshots/refactor-admin-mobile.png) |
| Staff | [Ảnh](screenshots/refactor-staff-desktop.png) | [Ảnh](screenshots/refactor-staff-tablet.png) | [Ảnh](screenshots/refactor-staff-mobile.png) |

Ảnh thêm: [Admin thu gọn](screenshots/refactor-admin-collapsed.png),
[Staff thu gọn](screenshots/refactor-staff-collapsed.png),
[Menu Staff mobile](screenshots/refactor-staff-menu-mobile.png),
[Staff bị 403](screenshots/refactor-staff-403-desktop.png).
Ảnh giai đoạn 3 ban đầu được giữ để đối chiếu. Đây là viewport mô phỏng trên
Chromium thật, chưa kiểm tra thiết bị cảm ứng vật lý, Safari/Firefox hoặc screen reader.

Lần chạy đầu phát hiện lỗi mất dấu khi ghi file qua PowerShell; đã sửa cách truyền
UTF-8 và xác minh lại. Hai locator browser đã điều chỉnh để theo dõi aria-label
thay đổi khi collapse và kiểm tra focus qua bàn phím thật. Không nới CSP hay bỏ
assertion. Không còn lỗi ghi nhận trong các kiểm tra bản cuối.

## Source code

Tạo mới:

- app/services/workspace_service.py: kiểm tra MySQL chỉ đọc.
- app/templates/layouts/workspace.html, layouts/staff.html: shell chung và menu Staff.
- app/templates/components/navigation.html: macro menu/section/trạng thái khóa.
- app/templates/admin/dashboard.html, staff/dashboard.html: hai Dashboard riêng.
- app/static/css/workspace.css: tokens, theme workspace, responsive/collapse.
- scripts/verify_demo_integrity.py, báo cáo này và docs/screenshots/refactor-*.png.

Chỉnh sửa:

- app/auth/permissions.py, auth/routes.py: quyền theo role và redirect.
- app/dashboard/routes.py, users/routes.py: route mới và alias tương thích.
- app/templates/layouts/admin.html, base.html, errors/error.html: layout mới và CSS scope.
- app/static/js/app.js: nút collapse có aria-expanded/aria-label.
- tests/test_auth.py, scripts/verify_ui.py: cập nhật hồi quy và browser checks.
- README.md, docs/ARCHITECTURE.md, AUTHENTICATION.md, SECURITY.md, DECISIONS.md,
  STAGE_3_REPORT.md: trạng thái và kiến trúc hiện tại.

Loại bỏ app/templates/admin/index.html và dashboard/index.html: hai trang cũ đã
được thay thế, route cũ vẫn tồn tại bằng redirect có kiểm tra quyền. Không đổi
models, CLI, seed, migrations, Docker Compose, Nginx hoặc dependencies runtime.

## Truy cập và bàn giao

Mở http://localhost:8000/login và dùng Admin đã tạo; không phải tạo lại tài khoản.
Login tự chuyển tới http://localhost:8000/admin/dashboard. Staff hiện được kiểm
tra bằng account riêng trong test DB, không tự thêm Staff vào database demo hoặc
đổi role Admin để demo. Khi có tài khoản Staff active được cấp hợp lệ, Login tự
chuyển tới http://localhost:8000/staff/dashboard.

Demo db/web/nginx healthy sau build lại web; kiểm tra check-db, db current và
db check thành công. Test services được stop sau nghiệm thu, giữ nguyên volumes.
Git diff --check không có lỗi whitespace; thay đổi chỉ thuộc refactor/tài liệu/
kiểm thử và ảnh minh chứng. Chưa tạo commit hoặc push đợt refactor này. Đề xuất:
`refactor(ui): separate admin and staff workspaces`.

Chưa có CRUD, công cụ quản trị sửa dữ liệu, nghiệp vụ kho/bán hàng, KPI hoặc báo
cáo doanh thu. Dừng tại giai đoạn 3, chờ người dùng xác nhận trước giai đoạn 4.
