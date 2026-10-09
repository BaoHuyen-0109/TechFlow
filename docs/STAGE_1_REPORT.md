# Báo cáo giai đoạn 1 — 09/10/2026

## Trạng thái

**Đã hoàn thành nghiệm thu nền tảng giai đoạn 1**, bao gồm build/start Docker,
kết nối MySQL thật, HTTP qua Nginx và giữ dữ liệu sau restart MySQL. Docker Engine
đã hoạt động sau khi người dùng mở Docker Desktop. Chờ xác nhận trước giai đoạn 2.

## Đã triển khai

- Git repository local, nhánh main; chưa tạo commit, remote hoặc đẩy lên GitHub.
- Flask app factory; environment development/testing/production; không fallback secrets.
- SQLAlchemy, Flask-Migrate, Flask-Login và CSRF extensions. Context người dùng của
  Flask-Login chưa bật vì user model/loader thuộc giai đoạn 2–3.
- `GET /`: trang thông tin nền tảng tiếng Việt bằng Jinja2/CSS tùy chỉnh, navy và xanh dương.
- `GET /health`: liveness JSON tối thiểu. Không truy vấn DB hoặc tiết lộ secrets.
- `flask --app wsgi check-db`: SELECT 1, thông báo tiếng Việt, exit 1 khi lỗi.
- Error handlers 400/403/404/413/500, security headers, logging ra stderr/stdout.
- Dockerfile Python 3.12 non-root + Gunicorn; Compose web/db/nginx; MySQL 8.0,
  utf8mb4, named volume, network backend nội bộ, health checks và restart policy.
- Chỉ Nginx publish 127.0.0.1; MySQL không publish, web không nhận root password.
- Runner test riêng, không kết nối database development.
- Package dành sẵn cho các module tiếp theo; không có route/nút nghiệp vụ giả.
- README, Git workflow, kiến trúc, quyết định kỹ thuật, bảo mật và xử lý Docker.

## File đã tạo

```text
.git/                                  # Metadata khởi tạo repository
.gitignore
.dockerignore
.env.example
Dockerfile
docker-compose.yml
docker-compose.test.yml
scripts/verify_local_storage.py
requirements.txt
requirements-dev.txt
pytest.ini
wsgi.py
README.md
app/__init__.py
app/config.py
app/extensions.py
app/cli.py
app/errors.py
app/main/__init__.py
app/main/routes.py
app/models/__init__.py
app/services/__init__.py
app/services/health_service.py
app/auth/__init__.py
app/dashboard/__init__.py
app/categories/__init__.py
app/businesses/__init__.py
app/products/__init__.py
app/purchases/__init__.py
app/sales/__init__.py
app/users/__init__.py
app/audit/__init__.py
app/templates/base.html
app/templates/main/index.html
app/templates/errors/error.html
app/static/css/foundation.css
app/static/js/.gitkeep
app/static/img/.gitkeep
nginx/default.conf
tests/conftest.py
tests/test_config.py
tests/test_foundation.py
tests/test_health_service.py
docs/ARCHITECTURE.md
docs/DECISIONS.md
docs/GIT_WORKFLOW.md
docs/DOCKER_TROUBLESHOOTING.md
docs/SECURITY.md
docs/STAGE_1_REPORT.md
```

Virtualenv `.venv/` được tạo để chạy test, bị ignore. Đã tạo `.env` local từ mẫu
với ba secrets ngẫu nhiên độc lập (mỗi giá trị 32 bytes, biểu diễn hex); không in
giá trị ra log. `.env` bị Git ignore và không nằm trong image. File đặc tả giữ nguyên.

## Kết quả kiểm thử thực tế

Môi trường: Windows, Python 3.12.7 trong virtualenv; Docker Desktop 4.84.0,
Engine 29.6.2 linux/amd64; image ứng dụng Python 3.12.12.

| Kiểm tra | Kết quả |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest --tb=short` | **16 passed**, 0.22s |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements found |
| `.\.venv\Scripts\python.exe -m compileall -q app tests wsgi.py` | Thành công |
| `docker compose config --quiet` với biến môi trường tạm | Thành công, chỉ kiểm tra cấu hình |
| `docker compose -f docker-compose.test.yml config --quiet` | Thành công, chỉ kiểm tra cấu hình |
| HTTP thật bằng server Werkzeug tạm trên loopback | `/` và `/health` trả HTTP 200; server đã dừng |
| `check-db` với cổng DB cố ý không khả dụng | Exit 1, thông báo an toàn, không lộ chi tiết kết nối |
| Docker Engine | Kết nối Client/Server thành công |
| `docker compose up --build -d --wait --wait-timeout 240` | Build thành công; db, web, nginx healthy |
| `docker compose exec -T web flask --app wsgi check-db` | Kết nối MySQL 8.0.44 thành công, kể cả sau restart |
| HTTP qua Nginx tại localhost:8000 | `/` và `/health` trả 200; health JSON đúng |
| `docker compose -f docker-compose.test.yml run --rm tests` | **16 passed**, 0.21s, không cảnh báo |
| `.\.venv\Scripts\python.exe scripts/verify_local_storage.py` | Dòng probe commit thành công và giữ nguyên sau restart MySQL |
| `docker compose exec -T nginx nginx -t` | Cấu hình Nginx hợp lệ |
| User chạy web | uid=999(app), không phải root |
| Charset/collation/engine MySQL | utf8mb4 / utf8mb4_unicode_ci / InnoDB |
| Cổng DB và backend network | Không có host port bindings; backend internal=true |
| Secrets trong image web | Không có .env, .venv hoặc MYSQL_ROOT_PASSWORD |
| Kiểm tra giao diện bằng browser desktop/tablet/mobile | **Chưa thực hiện trực quan**; layout quản trị thuộc giai đoạn 3 |

Tests bao phủ: secret thiếu/yếu/mẫu, môi trường không hợp lệ, password DB thiếu,
driver MySQL, URL-encoding password, cookie production, health không truy vấn DB,
trang thông tin/static, security headers, 404/500, CSRF, CLI thành công/thất bại
bằng mock, SELECT 1 và đóng connection. Không coi các mock là bằng chứng MySQL hoạt động.

Lần chạy đầu phát hiện thiếu Flask-Login user loader khi render template. Đã sửa bằng
cách chưa bật user context processor ở giai đoạn 1; toàn bộ 16 test cuối cùng đã đạt.

Lần đầu chạy test trong container có cảnh báo pytest không ghi được cache vào /app
vì user non-root. Đã chuyển cache sang `/tmp/techflow-pytest-cache` trong Compose test;
lần chạy cuối đạt 16/16 không cảnh báo. Không thay đổi quyền của ứng dụng để chạy test.

## Dữ liệu kiểm tra lưu trữ

Script tạo bảng phụ `stage1_probe` và giữ lại một dòng với id `367209152` để đối chiếu,
không sửa/xóa dữ liệu có sẵn. Bảng này không thuộc mô hình nghiệp vụ. Khi bổ sung
Alembic ở giai đoạn 2 cần loại bảng probe khỏi autogenerate, không sinh migration
xóa bảng này ngoài ý muốn. Các container và volume được giữ lại để người dùng xem.

## Việc còn cần người dùng thực hiện

1. Mở http://localhost:8000 để kiểm tra trang thông tin TechFlow. Đây chưa phải
   Dashboard hoặc màn hình đăng nhập; các chức năng này thuộc các giai đoạn sau.
2. `.env` đã được tạo; giữ file riêng trên máy. Có thể dừng services bằng
   `docker compose stop` khi không cần dùng, hoặc `docker compose start` để bật lại.
3. Nếu Git bằng tài khoản Dell báo dubious ownership, xem exception giới hạn đúng
   workspace tại `docs/GIT_WORKFLOW.md`. Thử đổi owner bằng tài khoản hiện tại bị
   Windows từ chối; không sửa Git global hay quyền truy cập rộng.

Không còn lỗi chặn vận hành Docker local trong các kiểm tra đã chạy. Chưa kiểm tra
giao diện trực quan trên browser nhiều kích thước; không coi trang nền tảng là UI
quản trị hoàn chỉnh. Git ownership vẫn có thể cần exception giới hạn như trên.
Không thực hiện AWS, không tạo tài nguyên phát sinh phí. Chờ người dùng kiểm tra
và xác nhận trước khi triển khai giai đoạn 2.
