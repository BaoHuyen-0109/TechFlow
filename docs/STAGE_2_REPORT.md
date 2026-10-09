# Báo cáo giai đoạn 2 — Database TechFlow

Ngày thực hiện: 09/10/2026 (Asia/Ho_Chi_Minh).

**Hoàn thành giai đoạn 2.** Đã triển khai và kiểm thử database bằng MySQL 8.0.44
trong Docker, áp dụng migration và seed lên database demo. Chờ xác nhận trước
giai đoạn 3; chưa triển khai đăng nhập hoặc nghiệp vụ nhập/bán hàng.

## Schema và quan hệ

Đủ 10 bảng: `users`, `businesses`, `categories`, `products`, `purchase_receipts`,
`purchase_receipt_items`, `sales_orders`, `sales_order_items`, `stock_movements`,
`audit_logs`. Có 12 FK, tất cả ON DELETE RESTRICT; PK/FK BIGINT UNSIGNED,
quantity INT UNSIGNED, tiền DECIMAL(14,2), InnoDB/utf8mb4_unicode_ci.

- Danh mục 1–N sản phẩm; nhà cung cấp 1–N sản phẩm và phiếu nhập.
- Phiếu nhập 1–N dòng phiếu; đơn bán 1–N dòng đơn; sản phẩm liên kết các dòng này.
- Sản phẩm 1–N lịch sử kho; user 1–N phiếu nhập, đơn bán, lịch sử kho, audit.
- Sản phẩm có nhà cung cấp nullable; audit có user nullable.
- Unique: username/email, mã NCC/mã số thuế, mã/tên danh mục, SKU, mã phiếu, mã đơn.
- CHECK: role/status/types, tiền không âm, số lượng dòng >0 và tổng dòng đúng.
- Indexes theo FK, tên/trạng thái sản phẩm, ngày/trạng thái giao dịch và reference/entity.

ERD và các quyết định: [DATABASE.md](DATABASE.md).
Toàn bộ cột, kiểu và constraints: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## Migrations

Revision: `db55d828848e_initial_ten_business_tables.py`, parent `None`.

1. Sinh và rà soát migration tạo 10 bảng; không có thao tác upgrade xóa probe.
2. Khởi tạo project `techflow-db-tests` với database MySQL rỗng, chạy upgrade thành công.
3. Chạy suite tích hợp đến khi đạt, sau đó upgrade database demo đang có stage1_probe.
4. `flask --app wsgi db current`: `db55d828848e (head)`.
5. `flask --app wsgi db check`: `No new upgrade operations detected.`

Alembic dùng bộ lọc bảo vệ stage1_probe và bảng reflected không thuộc metadata.
Database demo có 12 bảng vật lý: 10 nghiệp vụ + alembic_version + stage1_probe.
Đối chiếu toàn bộ một dòng probe trước/sau upgrade và seed: dữ liệu giống hệt,
id `367209152` giữ nguyên. Không xóa database/volume, không chạy downgrade.

## Seed demo

| Bảng | Lần đầu tạo mới | Lần hai tạo mới | Số lượng thực tế trong demo |
| --- | --- | --- | --- |
| categories | 6 | 0 | 6 |
| businesses | 6 | 0 | 6 |
| products | 36 | 0 | 36 |

6 danh mục: Laptop, Linh kiện máy tính, Màn hình, Thiết bị ngoại vi, Thiết bị mạng,
Phụ kiện. NCC, thương hiệu, giá và thông số ghi rõ giả lập; email example.invalid.
Seed chỉ insert theo code/SKU và không cập nhật bản ghi đã có. Test xác nhận tên/giá
đã chỉnh vẫn giữ nguyên khi chạy seed lại.

Tổng tồn kho = 0. Các bảng purchase/sales/items/movements/audit của database demo
đều đang rỗng. Không tạo giao dịch, tồn kho hay doanh thu giả. Dữ liệu giao dịch trong
test chỉ là fixture schema trên database test riêng, không nằm trong demo.

## CLI Admin

```powershell
docker compose exec web flask --app wsgi create-admin --username admin --full-name "Quản trị TechFlow"
```

Mật khẩu được nhập tại prompt ẩn hai lần, dài 12–128 ký tự; hash scrypt.
Email tùy chọn bằng `--email`. CLI validate username/name/email/password, từ chối
username/email trùng, ghi user và audit trong một transaction; không reset tài khoản
trùng, không in mật khẩu hoặc exception database. Có hỗ trợ môi trường
TECHFLOW_ADMIN_PASSWORD cho trường hợp cấp secret có kiểm soát, không có password argument.

Database demo hiện **0 user**; người dùng chọn mật khẩu khi tạo Admin bằng lệnh trên.
CLI đã được kiểm thử tạo user thành công, hash/verify password, duplicate, validation,
audit và prompt ẩn trên MySQL test. Chưa có màn hình đăng nhập ở giai đoạn 2.

## Kiểm thử

| Kiểm tra | Kết quả |
| --- | --- |
| Kiểm thử giai đoạn 1 trước khi thay đổi | 16/16 đạt; website và DB bình thường |
| Migration trên MySQL test rỗng | Thành công, đủ 10 bảng |
| Bộ test tổng hợp sau cùng | **45 passed in 3.37s**, không warning |
| So sánh schema migrated với models | Không có khác biệt |
| Constraints thực tế | Chặn SKU trùng, giá/tồn âm, FK sai, quantity=0, tổng dòng sai, role/status/type sai |
| Quan hệ và bảo toàn lịch sử | Các relation load được; xóa parent bị RESTRICT kể cả relation đã load |
| Số thập phân, Unicode, defaults | Đúng DECIMAL, utf8mb4, stock=0/reorder=5 và timestamp |
| Transaction lỗi | Rollback toàn bộ bản ghi thử nghiệm |
| Seed chạy lại | Không trùng, không ghi đè dữ liệu đã sửa |
| CLI Admin | Tạo/verify hash, validate, duplicate, audit, prompt ẩn đều đạt |
| Bảo vệ probe | Upgrade lặp và schema comparison không xóa/sửa probe |
| Database demo | Migration head, check-db thành công, seed đúng số lượng |
| Docker/HTTP sau cập nhật | 3 service healthy, `/` và `/health` HTTP 200 |
| Cú pháp Python | compileall app/tests/scripts/migrations/wsgi.py thành công |

Suite gồm 16 bài nền tảng và 29 bài bổ sung; tests MySQL chỉ chạy khi bật runner riêng.
Lệnh tái lập:

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
docker compose -f docker-compose.db-test.yml stop db-test
```

Project test có DB/user/network/volume riêng, không publish cổng, không gắn volume demo.
Không create_all/drop_all hoặc reset DB. Dữ liệu test dùng mã ngẫu nhiên và được giữ
trong volume test để không cần xóa dữ liệu sau mỗi lần chạy.

Lần chạy đầu có 6 test fail vì PyMySQL phân loại CHECK violation 3819 là
OperationalError thay vì IntegrityError như kỳ vọng test ban đầu. Đã sửa test
kiểm tra đúng mã 3819; không nới constraints. Template Alembic ban đầu dùng
get_engine deprecated, đã cập nhật sang engine; lần chạy cuối không warning.

## File tạo mới

```text
app/models/base.py
app/models/user.py
app/models/business.py
app/models/category.py
app/models/product.py
app/models/purchase.py
app/models/sale.py
app/models/stock_movement.py
app/models/audit_log.py
app/services/account_service.py
app/services/seed_service.py
app/migration_policy.py
migrations/README
migrations/alembic.ini
migrations/env.py
migrations/script.py.mako
migrations/versions/db55d828848e_initial_ten_business_tables.py
docker-compose.db-test.yml
tests/test_database.py
scripts/export_database_schema.py
docs/DATABASE.md
docs/DATABASE_SCHEMA.md
docs/STAGE_2_REPORT.md
```

## File chỉnh sửa

```text
app/__init__.py                 # Import metadata models
app/models/__init__.py          # Export đủ models
app/config.py                  # MySQL session UTC, hide SQL parameters
app/cli.py                     # create-admin, seed-demo
app/templates/main/index.html  # Cập nhật thông tin giai đoạn, không thêm UI nghiệp vụ
Dockerfile                     # Copy migrations vào image
tests/conftest.py              # Fixtures MySQL test biệt lập
README.md                      # Cách migration, seed, Admin, tests
docs/ARCHITECTURE.md
docs/DECISIONS.md
```

File đặc tả, secrets .env, Docker volume và dữ liệu stage1_probe được giữ nguyên.
Không sửa requirements hoặc thay đổi stack công nghệ. Chưa commit/push repository.

## Giới hạn và bước tiếp theo

- Không còn lỗi chặn trong phạm vi database đã kiểm thử.
- Chưa có login/layout quản trị, CRUD, nhập kho/bán hàng hoặc AWS.
- Stock movement/audit append-only hiện là quy ước ứng dụng, chưa có DB trigger.
- Header totals, tham chiếu đa loại, state transitions và đồng thời kho phải được
  xử lý/test ở service nghiệp vụ cuối kỳ; schema không tự triển khai các thao tác này.
- MySQL DDL không transactional toàn bộ; không thử downgrade vì có thể mất dữ liệu.
- Git ownership từ giai đoạn 1 vẫn có thể cần safe.directory giới hạn workspace,
  xem GIT_WORKFLOW.md; không sửa cấu hình Git global.

Website demo tiếp tục chạy tại http://localhost:8000. MySQL test đã được dừng sau
nghiệm thu để tiết kiệm RAM, volume test giữ lại. Dừng ở đây chờ người dùng xác nhận.
