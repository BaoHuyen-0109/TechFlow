# Bảo mật nền tảng và vận hành local

- SECRET_KEY bắt buộc và không có fallback. Secrets được cấp qua môi trường.
- `.env`, keys, dumps, instance và virtualenv bị ignore trong Git/Docker context.
- Ứng dụng chạy non-root trong image. Debug tắt; Gunicorn xử lý HTTP nội bộ.
- CSRFProtect được bật toàn cục. Chưa có form nghiệp vụ ở giai đoạn 1.
- Cookie HttpOnly, SameSite=Lax; production bắt buộc Secure và HTTPS.
- Không log connection URL, mật khẩu, cookie hoặc chi tiết exception DB.
- Health endpoint chỉ trả trạng thái ứng dụng; DB check nằm ở CLI.
- Nginx giới hạn body 1 MB, timeout; backend bổ sung nosniff, DENY frame và referrer policy.
- Chỉ publish loopback của Nginx. DB root password không được cấp cho web.
- Named volume không phải backup. Không dùng `down -v`, reset Docker hoặc xóa volume
  để sửa lỗi khởi động. Backup/restore trên database test sẽ bổ sung khi có schema.
- `DATABASE_URL` có thể override cấu hình; chỉ trỏ đến database demo khi chạy local.
- Không tạo tài nguyên hoặc cấu hình credentials AWS ở giai đoạn 1.

Trước khi public cuối kỳ cần review dependency/image, HTTPS, proxy trust, secrets,
đăng nhập/rate limit, permissions và backup/restore đã được kiểm thử. Các phần này
không được coi là hoàn tất chỉ vì có config production trong Python.
