# Báo cáo Giai đoạn 4 — TechFlow

Đợt hoàn thiện UI/UX sau báo cáo này: [STAGE_4_UI_REPORT.md](STAGE_4_UI_REPORT.md).
Số liệu kiểm thử và ảnh dưới đây là lịch sử lần triển khai CRUD ban đầu.

Ngày hoàn tất: 10/10/2026 (giờ Việt Nam). Phạm vi: CRUD danh mục, nhà cung cấp,
sản phẩm. Đã cập nhật ứng dụng local, **chưa commit/push Giai đoạn 4**, dừng chờ duyệt.

## Phần A — Git Giai đoạn 3

- Đã kiểm tra nhánh main, remote và lịch sử. Giai đoạn 1–2 nằm trong `abb05e5`;
  authentication ban đầu nằm trong `14f0a52`.
- Trước commit chạy 85 tests đạt và Playwright 6 tổ hợp role/viewport đạt.
  Kiểm tra diff và quét các secrets thật từ `.env` trong các file Git-visible đạt;
  `.env`, cache, virtualenv và dữ liệu tạm được loại trừ.
- Commit: `09e9c4ba4f9bdefa7fbd6516e0f2911da79bd8b7` —
  `feat: complete authentication and role-based dashboards`.
- Đã push main tới `https://github.com/BaoHuyen-0109/TechFlow.git`, xác minh
  `git ls-remote origin refs/heads/main` khớp commit local. Không force push/reset.
- Chỉ bắt đầu Giai đoạn 4 sau khi commit/push thành công. Các thay đổi bên dưới
  nằm trong working tree, không nằm trong commit Giai đoạn 3.

## Chức năng hoạt động thật

| Module | Chức năng |
| --- | --- |
| Danh mục | Danh sách/chi tiết/thêm/sửa/xóa, tìm mã/tên, sort, trạng thái, phân trang |
| Nhà cung cấp | CRUD đầy đủ, tìm mã/tên/email/phone, sort/trạng thái/phân trang, số sản phẩm/phiếu nhập liên kết |
| Sản phẩm | CRUD đầy đủ, SKU/tên, lọc danh mục/nhà cung cấp/trạng thái, sort/phân trang, giá VND, brand/model, ngưỡng cảnh báo, URL ảnh/mô tả |

Các thao tác lưu vào MySQL, thông báo tiếng Việt, POST/redirect/GET sau thành
công. Có validation backend, duplicate/FK error, 404, empty state, trạng thái
loading và modal xác nhận xóa. Dữ liệu có liên kết không bị xóa dây chuyền;
sản phẩm còn tồn kho không được xóa. Có thể sửa trạng thái ngừng hoạt động.

Menu Sản phẩm/Danh mục/Nhà cung cấp trong Business hoạt động; shortcut Sản phẩm
đã mở khóa. Sidebar navy và hai Dashboard riêng được giữ. Admin có liên kết
quay về quản trị, Staff không có và bị 403 tại backend khi mở URL quản trị.
CRUD của cả hai vai trò dùng cùng business_required. Chính sách Staff CRUD mới
thay quyền chỉ xem của đặc tả gốc trong ba module; đã báo cáo trước khi áp dụng.

Tồn kho chỉ đọc; sản phẩm mới stock=0, sửa sản phẩm không nhận stock_quantity từ
client. Không tạo stock movement, phiếu nhập, đơn bán hoặc KPI/doanh thu giả.
Nhà cung cấp chỉ đọc lịch sử tối đa 10 phiếu nhập nếu DB đã có; không xử lý phiếu.
Hình minh họa mặc định là SVG nội bộ; URL ảnh hợp lệ mở qua link, không server fetch.

## Routes và cấu trúc code

Ba prefix: `/business/categories`, `/business/suppliers`, `/business/products`.
Với mỗi prefix:

| Route | Phương thức |
| --- | --- |
| prefix | GET danh sách |
| /{id} | GET chi tiết |
| /new | GET form, POST tạo |
| /{id}/edit | GET form, POST sửa |
| /{id}/delete | POST xóa + CSRF |

Routes/form/service/model/template tách riêng. Ba Blueprint khai báo tại module
tương ứng, dùng catalog/resources cho cấu hình và bộ routes/templates chung.
Service có whitelist form fields, ORM, audit và transaction; không sửa models.
Chi tiết query, HTTP status, validation và quy tắc mở rộng tại [CATALOG.md](CATALOG.md).

## File tạo mới và chỉnh sửa

File mới:

- `app/catalog/__init__.py`, `forms.py`, `resources.py`, `routes.py`.
- `app/categories/routes.py`, `app/businesses/routes.py`, `app/products/routes.py`.
- `app/services/catalog_service.py`.
- `app/templates/catalog/base.html`, `index.html`, `form.html`, `detail.html`, `delete_modal.html`.
- `app/static/css/catalog.css`, `app/static/images/product-placeholder.svg`.
- `tests/test_catalog.py`, `tests/test_catalog_forms.py`.
- `scripts/verify_catalog_ui.py`.
- `docs/CATALOG.md`, `docs/STAGE_4_REPORT.md`.
- 36 ảnh CRUD `docs/screenshots/stage4-*.png` và 24 ảnh hồi quy có prefix
  `stage4-regression-`; ảnh lịch sử Giai đoạn 3 giữ nguyên.

File chỉnh sửa:

- `app/__init__.py`: đăng ký Blueprint, filter VND bằng Decimal.
- `app/static/js/app.js`: modal xóa dùng textContent và URL do server sinh.
- `app/templates/layouts/staff.html`: menu ba module thật.
- `app/templates/staff/dashboard.html`: shortcut Sản phẩm và trạng thái phù hợp.
- `app/templates/admin/dashboard.html`: bảng quyền CRUD mới.
- `app/templates/errors/error.html`: giữ Business layout khi lỗi ở /business/.
- `scripts/verify_ui.py`: kiểm tra link CRUD mới, cho phép prefix ảnh hồi quy riêng.
- `README.md`, `docs/ARCHITECTURE.md`, `docs/AUTHENTICATION.md`,
  `docs/DECISIONS.md`, `docs/SECURITY.md`: chạy app, kiến trúc, quyền và bàn giao.

Không đổi requirements, Docker Compose, models, migration, `.env` hoặc spec gốc.

## Database và migrations

- `categories`: code/name unique; một danh mục có nhiều sản phẩm.
- `businesses`: code/tax_code unique; một nhà cung cấp có nhiều sản phẩm/phiếu nhập.
  Schema không có cột loại đối tác, nên giao diện chỉ quản lý nhà cung cấp.
- `products`: SKU unique, category bắt buộc, nhà cung cấp tùy chọn;
  giá Numeric(14,2), stock/reorder unsigned, FK RESTRICT tới các quan hệ hiện có.
- `audit_logs`: create/update/delete có user_id, entity_type tên bảng, entity_id,
  nội dung cố định; không sao chép thông tin liên hệ hoặc secret vào audit.

Không cần migration mới. `db current`: **db55d828848e (head)**.
`db check`: **No new upgrade operations detected**. Test runner chạy `db upgrade`
thành công trên MySQL test hiện có, không reset/drop/create_all.

Đã tạo fingerprint chỉ đọc trước triển khai và đối chiếu sau khi rebuild demo:
**12/12 bảng có số dòng và SHA-256 giống hệt**. Dữ liệu chính vẫn 6 danh mục,
6 nhà cung cấp, 36 sản phẩm, 1 user, 4 audit; các bảng nhập/bán/movement đều 0.
`stage1_probe` vẫn 1 dòng. Không chạy seed-demo, sửa tài khoản hoặc xóa volume.
Snapshot `.docker-local/stage4-before.json` được ignore, không đưa vào Git.

## Kết quả kiểm thử

Lệnh:

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
```

Kết quả cuối: **135 passed in 38.46s**, không skip/fail trong runner MySQL.
Gồm 85 tests Giai đoạn 1–3, 39 integration tests CRUD mới và 11 unit tests form.
MySQL 8.0.44 thật, database `techflow_test`/host `db-test`, project/network/volume
tách demo. Test data có mã ngẫu nhiên, không cần reset khi chạy lại.

Đã kiểm tra:

- CRUD mỗi module với cả Admin/Staff, dữ liệu thực được lưu/sửa/xóa.
- Giá âm/NaN/Infinity/quá giới hạn/thừa thập phân, field trống/quá dài,
  email/phone/URL sai, ID liên kết không tồn tại.
- Duplicate mã/SKU/tên danh mục/tax_code; tax_code trống lưu NULL.
- FK danh mục/nhà cung cấp/sản phẩm, liên kết chi tiết phiếu nhập; không cascade.
- POST giả mạo tồn kho bị bỏ qua, số tồn giữ nguyên, không phát sinh nghiệp vụ.
- Audit đủ create/update/delete; lỗi audit/DB rollback bản ghi, không lưu dở dang.
- Authentication, inactive session, Staff403, CSRF create/edit/delete, GET delete405,
  missing record404, search/sort/pagination/filter, SQL injection và XSS.
- Toàn bộ regression auth/session/redirect/rate limit/seed/schema và nền tảng.

Các lần chạy đầu phát hiện lỗi render lại form sau duplicate và một test dùng tên
cố định gây trùng khi chạy lại; đã sửa. Không có lỗi test còn tồn tại ở lần chạy cuối.
Compile Python và `git diff --check` đạt; chỉ có cảnh báo quy đổi LF/CRLF của Git.
Đã quét secrets thật trong các file Git-visible, không phát hiện; `.env` bị ignore.

## Playwright và đánh giá UI

```powershell
docker compose -f docker-compose.db-test.yml --profile ui up -d --wait ui-nginx
docker compose -f docker-compose.db-test.yml exec -T ui-nginx nginx -s reload
.\.venv\Scripts\python.exe scripts/verify_catalog_ui.py
.\.venv\Scripts\python.exe scripts/verify_ui.py --screenshot-prefix stage4-regression
```

Chromium, hai vai trò × ba viewport **1440×1000, 834×1112, 390×844**:

- CRUD: **6/6 luồng đạt**, **18 vòng CRUD đầy đủ**, **72 POST có trạng thái loading**.
  Kiểm tra form, danh sách, chỉnh sửa, giá VND, lọc liên kết, modal hủy/xác nhận,
  chặn xóa dữ liệu đang dùng, validation và empty state sau xóa.
- Hồi quy workspace: **6/6 luồng đạt**. Login username/email, password toggle,
  logout, menu thật, active state, hover/focus bàn phím, sidebar collapse/offcanvas,
  Admin chuyển qua lại giữ phiên/role, Staff403 và trang404.
- Không phát hiện lỗi JavaScript, asset nội bộ bị lỗi hoặc tràn ngang toàn trang.
  Bảng mobile cuộn riêng; có hướng dẫn vuốt và region nhận focus bàn phím.
- Đã trực tiếp xem ảnh desktop, form tablet, danh sách mobile và modal mobile:
  typography/spacing đồng nhất, trường form không tràn, modal nằm trong màn hình,
  mã không bị ngắt dòng tùy tiện. Form dài và ảnh full_page có thể cao hơn viewport.

Ảnh cũ đã được dọn theo yêu cầu giảm screenshot. Xem [4 ảnh minh chứng hiện tại](screenshots/README.md); ảnh đã commit trước đây vẫn có trong lịch sử Git.

## Truy cập và giới hạn

Ứng dụng đã rebuild; web/db/nginx healthy, Nginx config test/reload đạt.
`check-db` kết nối thành công. HTTP local `/`, `/health`, `/login` trả200;
ba route catalog chưa đăng nhập trả302 đến Login. Services test được dừng sau
kiểm thử để tiết kiệm RAM, volume test vẫn giữ nguyên.

Mở http://localhost:8000/login, dùng tài khoản Admin và mật khẩu đã tạo trước đó.
Admin chọn **Không gian kinh doanh**, rồi **Sản phẩm/Danh mục sản phẩm/Nhà cung cấp**.
Không đặt mật khẩu mặc định, không đổi mật khẩu/role hoặc yêu cầu đăng nhập lại
khi chuyển workspace. Hướng dẫn kiểm tra CRUD trực tiếp ở [CATALOG.md](CATALOG.md).

Chưa kiểm tra Safari/Firefox hoặc thiết bị vật lý; browser test dùng Chromium với
viewport mô phỏng. Chưa có upload ảnh/export/bulk edit, màn hình audit hoặc cơ chế
phát hiện hai người sửa đồng thời (lần lưu sau thắng). Không có lỗi chức năng đã
biết trong phạm vi test hiện tại; chưa thực hiện kiểm thử tải/production.

Giai đoạn 5 sẽ xử lý phiếu nhập/đơn bán, hoàn tất/hủy giao dịch, transaction
cập nhật tồn kho, khóa hàng và chống xử lý lặp. Những phần này, thanh toán,
KPI/biểu đồ doanh thu, quản lý tài khoản và AWS **chưa triển khai**.

**Dừng tại đây để người dùng duyệt Giai đoạn 4. Không commit/push thay đổi mới.**
