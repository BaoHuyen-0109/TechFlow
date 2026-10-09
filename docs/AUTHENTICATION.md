# Authentication và Authorization — Giai đoạn 3

## Route và quyền

| Route | Truy cập | Hành vi |
| --- | --- | --- |
| GET /, /health | Công khai | Thông tin nền tảng/liveness |
| GET, POST /login | Công khai | Form CSRF, username hoặc email, password |
| GET /dashboard | Admin, Staff active | Layout và thông tin phiên thật |
| GET /admin | Admin active | Thông tin phạm vi quản trị; chưa có CRUD |
| POST /logout | Đã đăng nhập + CSRF | Audit, xóa phiên, về Login |
| GET /auth/rate-limit | Công khai | Trang 429 dùng cho Nginx limiter |

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

Mặc định về `/dashboard`. next chỉ chấp nhận chính xác `/dashboard` hoặc `/admin`;
URL ngoài, URL tương đối protocol, path khác đều về Dashboard. Staff theo next
`/admin` vẫn bị backend trả 403. Không có remember-me.

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
- `auth/permissions.py`: `@admin_required`, bao gồm login_required.
- `dashboard/routes.py`, `users/routes.py`: trang đã bảo vệ.
- `templates/layouts/admin.html`: sidebar, topbar, breadcrumb, POST Logout.
- `templates/components/flash.html`: thông báo dùng chung.
- `static/vendor`: Bootstrap/Icons/font nội bộ kèm license.
- `static/css/techflow.css`, `static/js/app.js`: theme, offcanvas, password toggle,
  submit loading và khôi phục trạng thái khi quay lại trang.

Module Admin ở giai đoạn sau phải dùng decorator backend, mọi form ghi dữ liệu
phải có CSRF token. Staff được cấp quyền theo ma trận đặc tả khi triển khai từng
module, không dùng việc ẩn menu làm kiểm tra quyền. Không thêm route CRUD giả.
Hiện Dashboard chỉ lấy thông tin current_user thật; chưa có số liệu kinh doanh.

## Kiểm thử và kiểm tra giao diện

`docker-compose.db-test.yml` dùng database techflow_test, DB_HOST=db-test, project
và volume riêng. Test không reset/drop database. Account ngẫu nhiên và audit test
được giữ trong volume test; demo không thay đổi. Profile ui dùng image runner đã
build, Nginx 127.0.0.1:8001 và cùng DB test. Playwright là công cụ host tùy chọn,
không cài vào image runtime. `scripts/verify_ui.py` có guard DB test trước khi
tạo account, không in credentials; chụp Login/Dashboard/Menu/Staff403.

Kết quả chi tiết và ảnh: [STAGE_3_REPORT.md](STAGE_3_REPORT.md). Không có migration
mới ở giai đoạn 3; tiếp tục revision db55d828848e và filter bảo vệ stage1_probe.
