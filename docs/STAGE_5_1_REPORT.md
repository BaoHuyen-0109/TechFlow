# TechFlow — Giai đoạn 5.1: khách hàng và lịch sử mua hàng

Ngày 10/10/2026 (Asia/Ho_Chi_Minh). Branch `feature/stage-5-1-customers` từ
`c4320cf985f505f3eca4d97f95c3d76e426d9343`. Chưa commit/push/merge main;
không triển khai Giai đoạn 7 hoặc AWS.

## Chức năng đã triển khai

- Hồ sơ khách: danh sách, tìm tên/phone/email, trạng thái, phân trang 10 dòng,
  thêm/xem/sửa, kích hoạt/vô hiệu hóa; không xóa cứng.
- Chuẩn hóa phone Việt Nam về +84 và UNIQUE cả inactive. Trùng số trả lỗi rõ,
  link hồ sơ sẵn có khi xác định được; không tự gộp hoặc tự chọn customer_id.
- Form đơn: vãng lai, chủ động chọn hồ sơ active, hoặc tạo khách mới trong đơn.
  Search gợi ý tối đa 20 hồ sơ, xem lịch sử tab khác; backend đọc lại hồ sơ và
  snapshot MySQL, bỏ qua thông tin tự điền khi chọn existing.
- Tạo khách + draft/items/audit trong cùng transaction. Draft không đổi kho;
  confirm/cancel, Decimal, khóa stock, CSRF, auth/session/ticket Stage 5 giữ nguyên.
- Hồ sơ: KPI completed count/spent/latest order_date, lịch sử 10 đơn/trang,
  dòng sản phẩm với quantity/unit_price/line_total snapshot, tổng hợp sản phẩm
  completed 10 dòng/trang. Draft/cancelled/vãng lai không vào chi tiêu.
- Admin quản lý hồ sơ, xem mọi trạng thái. Staff xem projection completed toàn
  cửa hàng, không notes/audit; không có link mở đơn khác owner. Route đơn bán
  của người khác vẫn 404, profile edit/status/new độc lập vẫn 403 cho Staff.
- Audit customer không lưu giá trị PII. Nginx access logs bỏ query/referrer để
  tránh ghi từ khóa tìm liên hệ. Không thay CSP hoặc nới nguồn script/style.

## Migration và bảo vệ dữ liệu demo

Revision `c051_customers` nối `db55d828848e`: thêm customers, customer_id nullable
FK RESTRICT, UNIQUE phone và indexes. 11 bảng nghiệp vụ, 14 FK; không backfill,
không sửa bốn trường snapshot hoặc bất kỳ trạng thái/tiền/tồn kho đơn cũ.

`verify_customer_migration.py` tạo hai schema test mới: migrate từ rỗng và
upgrade schema cũ có đơn draft/completed/cancelled. So sánh tất cả cột cũ của
đơn đạt, customer_id đều NULL, probe giữ nguyên. Không reset/drop schema/volume.

Trước migration demo: tạm stop Nginx để chặn thao tác ghi từ UI; web/db giữ
nguyên. Fingerprint/count 12 bảng khớp `.docker-local/stage51-before.json`.
Backup mới nhất trước nâng cấp:
`.docker-local/backups/stage51-20261010T093922Z-21cb76.sql` và manifest SHA-256
cùng tên `.json`. Dump single-transaction không chứa DROP TABLE, giữ local/
ignored. Đã restore vào schema mới trên db-test; cả 12 bảng fingerprint khớp.
Không in nội dung backup/password/hash tài khoản; không đưa backup vào Git.

Sau backup kiểm chứng, chạy một lần `docker compose run --rm --no-deps web
flask --app wsgi db upgrade`, rồi recreate riêng web và mở lại Nginx.
`verify_customer_demo_integrity.py` so các cột/bảng gốc (bỏ cột mới và revision)
đạt; users/audit/probe/catalog/giao dịch cũ giữ nguyên. `db check` không phát
hiện upgrade operations, Nginx config hợp lệ, login HTTP 200; services healthy.
Snapshot sau nâng cấp `.docker-local/stage51-after.json` có 13 bảng tổng cộng,
customers rỗng, 37 products, 6 categories, 6 suppliers, 1 user, 7 audit rows,
1 probe; chưa seed hoặc tạo giao dịch trên demo.

MySQL DDL có thể chờ metadata lock và không rollback như business transaction.
Downgrade phá dữ liệu customers/link bị chặn chủ động. Rollback app Stage 5 có
thể giữ schema bổ sung; recovery/forward fix phải được duyệt riêng.

## Kiểm thử

- Lượt regression đầu: 226 bài Stage 1–6 đạt 55.97s trên schema mới.
- Bộ khách hàng ban đầu: 25 bài đạt. Lượt toàn bộ tiếp theo: 258 bài đạt 60.90s,
  gồm 32 bài khách hàng (phone, multiple orders, snapshot, totals, duplicate,
  rollback, permissions, anonymous, CSRF, pagination và inactive).
- Bổ sung hai kịch bản quan trọng: tạo khách + đơn đồng thời cùng phone, và
  gửi lại order_code với phone khác phải rollback khách vừa chèn. Lượt cuối
  **260/260 bài đạt trong 64.29s**, gồm 226 regression và 34 bài khách hàng.
  Chạy sau khi browser hoàn tất để tránh ghi DB test chồng.
- Migration empty/legacy và backup restore MySQL thật đạt.
- Playwright khách hàng: 6 tổ hợp Admin/Staff × 1440×1000, 834×1112, 390×844 đạt.
  Kiểm tra tìm phone, lịch sử + KPI, không link mở đơn người khác, auto-fill,
  tạo/xác nhận đơn, inline create, duplicate 409, vãng lai NULL, Admin edit/
  deactivate và snapshot cũ không thay đổi. Không có pageerror.
- Regression nhập/bán: 6 tổ hợp và một no-JS draft đạt. Dashboard: 6 tổ hợp,
  2 lỗi chart fallback, 2 no-JS đạt. Workspace: 6 tổ hợp đạt.
- Script catalog được bổ sung chờ navigation sau GET filter trước khi đọc bảng,
  giữ nguyên assertions; không sửa chức năng catalog để xử lý timing của runner.
  Chạy lại đạt 6 tổ hợp, 18 chu trình CRUD và 72 kiểm tra POST/loading. Bộ
  filter/paging/profile đạt 18 luồng, kèm no-JS CRUD/precision/validation.
- compileall, git diff --check, scan Git-visible secrets/generated files đạt.

Lượt cuối có **42 file mới/sửa**, không staged, HEAD vẫn c4320cf; chưa commit,
push hoặc merge. Bản runtime cuối chỉ cập nhật thêm thông báo validation tiếng
Việt, không chạy lại migration. Login HTTP 200; 13 bảng sau migration vẫn khớp
fingerprint/count `.docker-local/stage51-after.json`.
Service test ui-nginx/ui/db-test đã stop sau kiểm thử; mọi volume/schema test
giữ nguyên. Demo web/db/nginx vẫn healthy, không đổi tài khoản hoặc secrets.

Lỗi trong phát triển đã sửa: macro import từ layout có context chưa phù hợp;
runner khách hàng ban đầu bỏ sót query string trên URL POST và tên fixture
category chưa unique. Các sửa này đã được chạy lại đạt; không reset dữ liệu test.

## File tạo mới/chỉnh sửa

Tạo mới:

- `app/customers/{__init__,forms,routes}.py`
- `app/models/customer.py`, `app/services/customer_service.py`
- `app/templates/customers/{base,index,form,detail,macros,order_picker}.html`
- `app/static/css/customers.css`, `app/static/js/customers.js`
- `migrations/versions/c051_customers.py`, `tests/test_customers.py`
- `scripts/verify_customers_ui.py`, `scripts/verify_customer_migration.py`,
  `scripts/backup_before_customers.py`, `scripts/verify_customer_demo_integrity.py`
- `docs/CUSTOMERS.md`, báo cáo này.

Chỉnh sửa:

- `app/__init__.py`, `app/models/{__init__,sale}.py`
- `app/purchases/{forms,views}.py`, `app/services/transaction_service.py`
- `app/templates/layouts/staff.html`, `app/templates/transactions/{base,form}.html`
- `nginx/default.conf`, `.gitignore`, `README.md`
- `tests/test_database.py`, `scripts/{verify_ui,verify_catalog_ui,export_database_schema}.py`
- `docs/{ARCHITECTURE,AUTHENTICATION,DATABASE,DATABASE_SCHEMA,DECISIONS}.md`

## Giao diện và hướng dẫn xem

Đăng nhập bằng tài khoản hiện có tại http://localhost:8000/login, chọn Không
gian kinh doanh → **Khách hàng**. Admin có **Thêm khách hàng**; Staff tạo khách
qua **Bán hàng và đơn bán → Tạo mới → Tạo hồ sơ khách mới**. Không tạo mật khẩu
mặc định hoặc thay tài khoản. Chọn hồ sơ → **Lập đơn cho khách** để thử snapshot.
Demo không được nạp fixture: số liệu ở screenshot là test riêng và được đánh dấu.

Giữ 2 ảnh đại diện hồ sơ khách: [desktop](screenshots/stage51-admin-desktop-profile.png) và [mobile](screenshots/stage51-admin-mobile-profile.png). Các ảnh luồng khác đã được dọn; kết quả kiểm thử bên trên giữ nguyên.

Ảnh dữ liệu test riêng; 2 ảnh đại diện được đưa vào commit 5.2 để xem được trên GitHub.

## Giới hạn

Phone validation chỉ kiểm tra định dạng VN, không OTP/xác minh nhà mạng; người
dùng chung số có thể lập đơn vãng lai. Không merge hồ sơ, gán lại đơn cũ, bulk
import/export hoặc khách quốc tế trong hồ sơ. Tên/SKU sản phẩm vẫn catalog hiện
tại; giá mua là snapshot đơn. Lần mua gần nhất là order_date, chưa completed_at.
No-JS có 20 hồ sơ đầu hoặc chọn từ trang hồ sơ; search gợi ý cần JS. Chưa kiểm
thử tải lớn, thiết bị vật lý, Safari/Firefox. Không giảm giá/điểm/xếp hạng/voucher.
Không ghi nhận lỗi chức năng còn tái hiện trong các luồng đã đạt.

Dừng chờ người dùng nghiệm thu trước commit/push hoặc Giai đoạn 7.

## Checkpoint được duyệt trước Giai đoạn 5.2

Người dùng đã cho phép commit baseline 5.1. Regression chạy lại trên MySQL test
Docker: 260/260 đạt trong 62.05s. Khôi phục 71 ảnh Git được tài liệu tham chiếu;
27 ảnh không được tham chiếu giữ trạng thái xóa theo yêu cầu dọn ảnh. Báo cáo 5/6
đã thay 28 liên kết ảnh local bị dọn bằng ghi chú, giữ mô tả kết quả kiểm thử.
8 ảnh minh chứng 5.1 vẫn local/ignored. Rà soát Git-visible không phát hiện
secrets, dump, database local hoặc file generated nhạy cảm; diff --check đạt.
Không thay đổi dữ liệu demo hoặc migration trong lượt chốt baseline này.

Baseline đã commit `d9e0295` với 71 file mới/sửa/xóa, chưa push hoặc merge main.
Branch Giai đoạn 5.2 được tạo từ checkpoint sạch này.
