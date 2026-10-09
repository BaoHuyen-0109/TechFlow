# Bảo mật nền tảng và vận hành local

- SECRET_KEY bắt buộc và không có fallback. Secrets được cấp qua môi trường.
- `.env`, keys, dumps, instance và virtualenv bị ignore trong Git/Docker context.
- Ứng dụng chạy non-root trong image. Debug tắt; Gunicorn xử lý HTTP nội bộ.
- CSRFProtect được bật toàn cục cho Login, Logout và các form ghi dữ liệu sau này.
- Cookie HttpOnly, SameSite=Lax; production bắt buộc Secure và HTTPS.
- Không log connection URL, mật khẩu, cookie hoặc chi tiết exception DB.
- Health endpoint chỉ trả trạng thái ứng dụng; DB check nằm ở CLI.
- Nginx giới hạn body 1 MB, timeout; backend bổ sung nosniff, DENY frame và referrer policy.
- Chỉ publish loopback của Nginx. DB root password không được cấp cho web.
- Named volume không phải backup. Không dùng `down -v`, reset Docker hoặc xóa volume
  để sửa lỗi khởi động. Backup/restore trên database test sẽ bổ sung khi có schema.
- `DATABASE_URL` có thể override cấu hình; chỉ trỏ đến database demo khi chạy local.
- Không tạo tài nguyên hoặc cấu hình credentials AWS ở giai đoạn 1.

Giai đoạn 3: Flask-Login strong session protection, xác minh is_active/role mỗi
request, backend admin_required/business_required, session.clear khi login/logout.
Admin được cả hai Dashboard; Staff bị chặn ở route Admin. Chuyển workspace là GET
đã xác thực, không tạo phiên mới hoặc đổi role.
Allowlist redirect gồm `/dashboard`, `/admin`, `/admin/dashboard`, `/staff/dashboard`;
sau login luôn chọn Dashboard chính xác theo role, kể cả next trỏ role khác.
HTML trả Cache-Control=no-store. CSP chỉ dùng
assets nội bộ, không cho inline script/eval. Password không xuất hiện trong form
render lại hoặc log; lỗi tài khoản không tồn tại/sai mật khẩu/inactive dùng chung
thông báo. Không có tài khoản mặc định.

Throttling lưu dấu thất bại HMAC trong audit_logs, dùng MySQL advisory lock để
tuần tự hóa theo tài khoản; không chỉ lưu bộ đếm trong RAM. Nginx giới hạn POST
Login 10 request/phút/IP, burst 5. App chưa tin forwarded headers: audit IP là IP
proxy, còn IP limiter dùng remote_addr tại Nginx. Không xóa audit đăng nhập trong
cửa sổ 15 phút nếu sau này bổ sung retention. Xem [AUTHENTICATION.md](AUTHENTICATION.md).

Session Flask lưu ở cookie đã ký; không lưu password và không phải dữ liệu mã hóa.
Logout xóa cookie hiện tại; chưa có kho phiên server để thu hồi riêng cookie đã bị
sao chép. Khóa tài khoản có hiệu lực ở request tiếp theo; đổi SECRET_KEY thu hồi
tất cả cookie và đồng thời đổi bucket HMAC. HTTP chỉ dùng local loopback.

Trước khi public cuối kỳ cần review dependency/image, HTTPS, proxy trust, secrets,
đăng nhập/rate limit, permissions và backup/restore đã được kiểm thử. Các phần này
không được coi là hoàn tất chỉ vì có config production trong Python.
