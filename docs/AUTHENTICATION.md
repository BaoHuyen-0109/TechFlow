# Authentication và Authorization — Giai đoạn 3

## Route và quyền

| Route | Truy cập | Hành vi |
| --- | --- | --- |
| GET /, /health | Công khai | Thông tin nền tảng/liveness |
| GET, POST /login | Công khai | Form CSRF, username hoặc email, password |
| GET /dashboard | Admin, Staff active | Redirect theo vai trò |
| GET /admin | Admin active | Redirect /admin/dashboard |
| GET /admin/dashboard | Admin active | Tài khoản, ma trận quyền, kết nối MySQL chỉ đọc |
| GET /staff/dashboard | Admin, Staff active | Không gian kinh doanh riêng, empty state |
| POST /logout | Đã đăng nhập + CSRF | Audit, xóa phiên, về Login |
| GET /auth/rate-limit | Công khai | Trang 429 dùng cho Nginx limiter |
| GET /business/categories, /business/suppliers, /business/products | Admin, Staff active | Danh sách, tìm kiếm/lọc/phân trang |
| GET /business/{module}/{id} | Admin, Staff active | Chi tiết |
| GET, POST /business/{module}/new, /{id}/edit | Admin, Staff active | Form CRUD, POST có CSRF |
| POST /business/{module}/{id}/delete | Admin, Staff active | Xóa có kiểm tra liên kết/tồn kho + CSRF |

Không có user mặc định. Tạo Admin bằng CLI trong README, prompt mật khẩu ẩn hai
lần. User.set_password dùng scrypt; authenticate dùng check_password_hash. Email
là tùy chọn khi tạo Admin. Username/email normalize ở đầu vào; password giữ nguyên.

## Luồng đăng nhập

LoginForm kiểm tra CSRF, identity bắt buộc tối đa 190 ký tự, password bắt buộc tối
đa 128 ký tự. Truy vấn ORM username OR email, kiểm tra hash và is_active/role.
Unknown user vẫn kiểm tra dummy scrypt hash để tránh nhánh bỏ qua hash. Các lỗi
tài khoản trả cùng thông báo tiếng Việt và HTTP 401. DB không sẵn sàng trả 503
không lộ exception. Thành công cập nhật last_login_at UTC, audit login_success,
xóa trạng thái phiên trước login rồi Flask-Login tạo phiên mới.

Sau login, Admin về `/admin/dashboard`, Staff về `/staff/dashboard`. Allowlist next
chỉ chấp nhận chính xác bốn đường dẫn Dashboard/alias trong bảng trên; URL ngoài,
URL tương đối protocol, path khác đều bị loại. Với phạm vi hiện tại tất cả next
được quy về trang chủ role của tài khoản vừa xác thực. Admin có thể mở trực tiếp
hoặc chuyển qua `/staff/dashboard`; Staff không qua được `/admin` hoặc
`/admin/dashboard`, kể cả sửa URL. Không có remember-me.

User loader tải MySQL ở request tiếp theo, từ chối inactive hoặc role ngoài
admin/staff. Việc đổi role có hiệu lực ở request tiếp theo. Strong session
protection của Flask-Login và session HttpOnly/SameSite=Lax được bật. Session
permanent sống 8 giờ, được gia hạn khi hoạt động theo Flask. Secure bắt buộc khi
APP_ENV=production, không phù hợp HTTP local. Logout chỉ POST với CSRF hợp lệ.

## Giới hạn đăng nhập sai

- App: 5 thất bại trong cửa sổ trượt 15 phút; request tiếp theo trả 429 và
  Retry-After=900. Thành công không xóa lịch sử thất bại trong cửa sổ.
- Account tồn tại dùng HMAC(SECRET_KEY, user:id), do đó username/email dùng chung
  bucket. Identity chưa tồn tại dùng HMAC của identity đã normalize. Không lưu
  password, token hoặc identity gốc trong bản ghi thất bại.
- AuditLog(action=login_failed, entity_type=auth_attempt, description=bucket)
  lưu bền trong MySQL. GET_LOCK với timeout 3 giây trên connection riêng giữ khóa
  đến khi commit attempt, RELEASE_LOCK trong finally. Khóa bận cũng trả 429.
  Test đồng thời dùng app context/connection độc lập, không chỉ một test client.
- Nginx: POST /login giới hạn 10r/m theo remote IP, burst=5 nodelay; GET Login
  không bị limiter này. Trang 429 thân thiện dùng cùng template lỗi của ứng dụng.
  App không bật ProxyFix; audit IP tại backend hiện là IP proxy. Không dùng header
  do client tự gửi để tính bucket. Trước public phải thiết kế proxy trust riêng.

Không xóa login_failed còn trong 15 phút khi bổ sung audit retention. Thay
SECRET_KEY thu hồi session cũ và đổi bucket HMAC. Đổi account active/role không
xóa audit. Giới hạn này phục vụ demo local, chưa có CAPTCHA/MFA, lockout quản trị
hay kiểm thử tải diện rộng.

## Tổ chức và mở rộng

- `auth/forms.py`: form và thông báo validation.
- `auth/routes.py`: request/session/redirect; không đặt SQL nghiệp vụ tại form.
- `services/auth_service.py`: hash, rate limit và audit transaction.
- `auth/permissions.py`: `@admin_required` (Admin) và `@business_required` (Admin,
  Staff), cùng dùng role_required và login_required; role khác bị 403.
- `dashboard/routes.py`, `users/routes.py`: trang đã bảo vệ.
- `templates/layouts/admin.html`, `staff.html`: sidebar/nhận diện workspace riêng.
- `templates/layouts/workspace.html`: shell/topbar/breadcrumb/POST Logout dùng chung.
- `templates/admin/dashboard.html`, `staff/dashboard.html`: hai trang chủ riêng.
- `templates/components/flash.html`: thông báo dùng chung.
- `static/vendor`: Bootstrap/Icons/font nội bộ kèm license.
- `static/css/techflow.css`, `static/js/app.js`: theme, offcanvas, password toggle,
  submit loading và khôi phục trạng thái khi quay lại trang.

Module Admin ở giai đoạn sau phải dùng decorator backend, mọi form ghi dữ liệu
phải có CSRF token. Theo yêu cầu Giai đoạn 4 mới, cả Admin và Staff được CRUD
danh mục/nhà cung cấp/sản phẩm; chính sách này thay quyền Staff chỉ xem của đặc tả
ban đầu trong phạm vi ba module. Các route đều dùng business_required ở backend.
Staff vẫn không được quản trị user/role/cấu hình. Không dùng việc ẩn menu để kiểm tra quyền.
Dashboard quản trị lấy current_user và SELECT 1 kiểm tra kết nối. Dashboard
Business có thống kê catalog/tồn kho từ MySQL theo [DASHBOARD.md](DASHBOARD.md):
cả hai vai trò xem số lượng và danh sách catalog, chỉ Admin xem tổng giá trị tồn
kho. Backend không truy vấn giá nhập hoặc trả tổng giá trị trong payload Dashboard
của Staff; không thể mở quyền bằng query string. Quyền CRUD catalog giữ nguyên. Admin
được quyền cả hai không gian, Staff chỉ Business. Business giữ layout Staff ngay
cả khi Admin truy cập; topbar/phiên vẫn hiển thị role thật, breadcrumb và brand
trỏ trang chủ Business. Admin chuyển về quản trị qua liên kết riêng, Staff không
thấy liên kết đó. Hai liên kết chuyển workspace chỉ GET, không logout/login,
không đổi session user/role/CSRF, không tạo audit login mới. Module nghiệp vụ
tương lai phải sử dụng chính sách quyền backend tương ứng và validation riêng.

## Kiểm thử và kiểm tra giao diện

`docker-compose.db-test.yml` dùng database techflow_test, DB_HOST=db-test, project
và volume riêng. Test không reset/drop database. Account ngẫu nhiên và audit test
được giữ trong volume test; demo không thay đổi. Profile ui dùng image runner đã
build, Nginx 127.0.0.1:8001 và cùng DB test. Playwright là công cụ host tùy chọn,
không cài vào image runtime. `scripts/verify_ui.py` có guard DB test trước khi
tạo account, không in credentials; chụp Login/Dashboard/Menu/Staff403.

Kết quả ban đầu: [STAGE_3_REPORT.md](STAGE_3_REPORT.md). Refactor và ảnh mới:
[STAGE_3_REFACTOR_REPORT.md](STAGE_3_REFACTOR_REPORT.md). Không có migration
mới ở giai đoạn 3; tiếp tục revision db55d828848e và filter bảo vệ stage1_probe.

Chính sách quyền hiện tại và minh chứng Admin chuyển qua lại:
[STAGE_3_ACCESS_REPORT.md](STAGE_3_ACCESS_REPORT.md).

Thay đổi quyền và CRUD mới nhất: [CATALOG.md](CATALOG.md),
[STAGE_4_REPORT.md](STAGE_4_REPORT.md). Báo cáo Giai đoạn 3 giữ lại làm lịch sử.
