# TechFlow

Hệ thống quản lý kinh doanh thiết bị công nghệ — đồ án Flask, Docker và Amazon EC2.
**Trạng thái: hoàn thành giai đoạn 3 — Authentication, Authorization & Admin Layout.**
Có đăng nhập username/email, phân quyền Admin/Staff và Dashboard responsive.
CRUD và các KPI kinh doanh chưa triển khai.
Không triển khai AWS trong giai đoạn này.

Đặc tả chính thức: [tech_business_manager_aws_spec.md](tech_business_manager_aws_spec.md).
Kết quả đã kiểm tra và giới hạn: [docs/STAGE_1_REPORT.md](docs/STAGE_1_REPORT.md).
Kết quả database: [docs/STAGE_2_REPORT.md](docs/STAGE_2_REPORT.md).
Kết quả đăng nhập và giao diện: [docs/STAGE_3_REPORT.md](docs/STAGE_3_REPORT.md).

## Yêu cầu

- Docker Desktop với Linux Engine đang chạy và Docker Compose.
- Internet để build images và cài dependencies.
- Cổng localhost 8000 trống (đổi APP_PORT nếu cần).

Nếu `docker version` chỉ có Client, làm theo
[hướng dẫn xử lý Engine](docs/DOCKER_TROUBLESHOOTING.md) trước khi chạy container.

## Chạy local bằng Docker (PowerShell)

```powershell
Set-Location E:\AWS
# Chỉ tạo .env khi chưa có; giữ nguyên secrets/database của dự án hiện tại.
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Điền SECRET_KEY (ít nhất 32 ký tự), MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD bằng
ba giá trị ngẫu nhiên khác nhau. Có thể tạo từng giá trị bằng PowerShell:

```powershell
$secretBytes = New-Object byte[] 32
$generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$generator.GetBytes($secretBytes)
[Convert]::ToBase64String($secretBytes)
$generator.Dispose()
```

Lặp lại để tạo các giá trị khác nhau, giữ chúng riêng trên máy. Đặt giá trị `.env`
trong dấu nháy đơn nếu chứa ký tự đặc biệt. Không commit `.env`. DATABASE_URL để
trống: app tự xây URL an toàn từ MYSQL_* và DB_HOST. Không đưa MYSQL_ROOT_PASSWORD
vào container web; user ứng dụng chỉ dùng database riêng.

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose exec web flask --app wsgi check-db
Invoke-RestMethod http://localhost:8000/health
```

Mở http://localhost:8000/login để đăng nhập; `/dashboard` yêu cầu xác thực.
Trang `/` vẫn là thông tin nền tảng công khai. `/health`
trả `{"status":"ok"}` khi Flask phản hồi; endpoint này không chứng minh DB hoạt động.
Lệnh `check-db` mới kiểm tra MySQL thực sự.

## Khởi tạo database và dữ liệu demo

Sau khi services healthy, chạy migration một lần có kiểm soát:

```powershell
docker compose exec web flask --app wsgi db upgrade
docker compose exec web flask --app wsgi db current
docker compose exec web flask --app wsgi db check
docker compose exec web flask --app wsgi seed-demo
```

Revision hiện tại `db55d828848e`. Seed chỉ thêm bản ghi thiếu, không reset dữ liệu;
chạy lại tạo mới 0 bản ghi nếu dữ liệu DEMO đã đủ. Database demo trên máy này đã
được upgrade và seed. Bảng stage1_probe và volume hiện tại được giữ nguyên.

Tạo Admin với mật khẩu do bạn chọn tại prompt ẩn (nhập hai lần, 12–128 ký tự):

```powershell
docker compose exec web flask --app wsgi create-admin --username admin --full-name "Quản trị TechFlow"
```

Email tùy chọn bằng `--email`. Không có mật khẩu mặc định; seed không tạo user.
Trùng username/email bị từ chối, không reset password. Dùng username `admin`
(hoặc email đã cung cấp) và mật khẩu vừa nhập tại trang Login. Không gửi mật khẩu
qua chat hoặc ghi vào command. Trên máy này chưa có Admin tại lần kiểm tra bàn giao;
bạn cần chạy CLI trên trước khi demo đăng nhập.

## Đăng nhập, phân quyền và giao diện

- Login bằng username/email không phân biệt hoa thường; mật khẩu được kiểm tra với
  hash scrypt trong MySQL. Tài khoản inactive bị chặn, kể cả phiên đã đăng nhập.
- Admin truy cập `/dashboard` và `/admin`; Staff chỉ truy cập Dashboard giới hạn.
  `/admin` hiện là trang xác nhận phạm vi quyền, chưa có CRUD tài khoản/cấu hình.
- Đăng xuất qua nút trên topbar bằng POST + CSRF. CSRF được bật toàn cục.
- Sai 5 lần trong 15 phút sẽ tạm chặn đăng nhập tài khoản, dùng chung giới hạn giữa
  username/email và giữa các Gunicorn workers. Nginx còn giới hạn POST Login theo IP.
- Session ký bằng SECRET_KEY, thời gian sống 8 giờ có gia hạn khi hoạt động;
  HttpOnly, SameSite=Lax, Secure bắt buộc ở production HTTPS. Local HTTP để Secure=false.
- Sidebar navy, nội dung sáng, Bootstrap Icons và assets Bootstrap lưu nội bộ.
  Module chưa triển khai hiển thị trạng thái; không có nút CRUD giả hay số liệu KPI giả.

Chi tiết bảo mật và tích hợp module sau: [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md).

Xem [schema và ERD](docs/DATABASE.md). Không chạy downgrade hoặc xóa volume trên
database đang dùng. `db check` so sánh schema với models, tự bỏ qua bảng probe.

```powershell
docker compose logs --tail 100 web nginx
docker compose stop
docker compose start
```

Để recreate sau khi sửa code: `docker compose up --build -d`.
Để dừng và gỡ container/network: `docker compose down` (giữ named volume).
Không thêm `-v`: thao tác này xóa dữ liệu volume.

## Kiểm thử

Tests nền tảng không kết nối DB hoặc tạo/xóa schema. Chạy trong runner biệt lập:

```powershell
docker compose -f docker-compose.test.yml run --build --rm tests
```

Hoặc dùng Python 3.12 local, không cần Docker để test Flask:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

Các bài database được skip khi chưa bật runner MySQL. Chạy đầy đủ trên MySQL riêng:

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
docker compose -f docker-compose.db-test.yml stop db-test
```

Runner áp dụng migration rồi chạy cả tests nền tảng và database. DB/network/volume
test tách khỏi demo; không xóa/reset database hay volume. Giữ dữ liệu test giữa các lần chạy.

Kiểm tra trình duyệt tùy chọn (Chromium; cần Python local và tải browser một lần):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
$env:PLAYWRIGHT_BROWSERS_PATH = 'E:\AWS\.browser-cache'
.\.venv\Scripts\python.exe -m playwright install chromium
# Chạy runner MySQL ở trên trước để có image test và schema.
docker compose -f docker-compose.db-test.yml --profile ui up -d --wait ui-nginx
.\.venv\Scripts\python.exe scripts/verify_ui.py
docker compose -f docker-compose.db-test.yml --profile ui stop ui-nginx ui db-test
```

Script chỉ tạo tài khoản có mật khẩu ngẫu nhiên trong DB test và lưu ảnh vào
`docs/screenshots`; không in credentials, không thay đổi demo. Kiểm tra ba viewport
desktop/tablet/mobile, menu, login/logout, 403/404 và tràn ngang. Khi image UI thay
đổi địa chỉ container, restart riêng `ui-nginx` nếu gặp 502.

Chạy app local tùy chọn: load `.env` qua wsgi rồi dùng
`.\.venv\Scripts\python.exe -m flask --app wsgi run --host 127.0.0.1 --port 8000`.
Chỉ dùng dev server local. MySQL trong Compose không publish cổng; app local muốn
kết nối DB cần MySQL riêng và DB_HOST/DATABASE_URL phù hợp. Docker là đường chạy chính.

## Kiểm tra lưu trữ sau khi Engine hoạt động

Agent đã chạy kiểm tra này trên Docker local; xem kết quả trong báo cáo giai đoạn 1.
Để chạy lại bằng script (tạo dòng probe, restart riêng service db, không xóa dữ liệu):

```powershell
.\.venv\Scripts\python.exe scripts/verify_local_storage.py
```

Bảng `stage1_probe` là bảng kiểm tra riêng, cần loại khỏi Alembic autogenerate khi
thiết lập migrations. Script giữ lại dòng probe để đối chiếu. Phương án kiểm tra thủ công:

Giai đoạn 1 chưa có bảng nghiệp vụ. Có thể kiểm tra volume với bảng probe tạm,
chạy thủ công trong MySQL CLI. Chỉ tạo bảng probe ở database local demo:

```powershell
docker compose exec db mysql -u techflow_app -p tech_business_db
```

Thay user/database theo `.env`; nhập password tại prompt, không truyền password
trong lịch sử command. Trong MySQL:

```sql
CREATE TABLE IF NOT EXISTS stage1_probe (id INT PRIMARY KEY, marker VARCHAR(50)) ENGINE=InnoDB;
INSERT INTO stage1_probe VALUES (1, 'techflow-volume-check');
exit
```

Chạy `docker compose restart db`, chờ db healthy, đăng nhập MySQL lại rồi:

```sql
SELECT * FROM stage1_probe;
```

Kết quả cần giữ nguyên marker. Bảng probe do bạn tạo có thể giữ để đối chiếu hoặc
xóa thủ công sau khi kiểm tra; ứng dụng không tự tạo/xóa bảng này.

## Tài liệu nhóm

- [Kiến trúc và ranh giới module](docs/ARCHITECTURE.md)
- [Các quyết định kỹ thuật](docs/DECISIONS.md)
- [Database và ERD](docs/DATABASE.md)
- [Git workflow và quy ước code](docs/GIT_WORKFLOW.md)
- [Bảo mật và vận hành local](docs/SECURITY.md)
- [Authentication và quyền truy cập](docs/AUTHENTICATION.md)

Giai đoạn tiếp theo chỉ bắt đầu sau khi người dùng xác nhận. AWS deployment,
HTTPS public, backup/restore nghiệp vụ và kiểm thử tải nằm ở giai đoạn sau;
Compose hiện tại dành cho localhost, không dùng trực tiếp để public website.
