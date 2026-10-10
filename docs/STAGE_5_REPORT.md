# TechFlow — Báo cáo Giai đoạn 5: Kho, bán hàng, khách hàng và bảo hành

Báo cáo hợp nhất nghiệp vụ Giai đoạn 5, nghiệm thu nhập/bán, khách hàng (5.1),
bảo hành/sidebar (5.2) và tinh chỉnh chi tiết giao dịch/bảo hành trước Giai đoạn 7.
Ngày tổng hợp: 10/10/2026, Asia/Ho_Chi_Minh. Giữ Flask/Jinja2/Bootstrap 5/MySQL/Docker.

Các số kiểm thử là kết quả của các lượt nghiệm thu đã thực hiện, không phải lượt
chạy mới khi gộp tài liệu. Phần UI cuối và việc gộp doc nằm trên branch
`feature/ui-ux-before-stage-7`. Các checkpoint 5/5.1/5.2 đã
được lưu; main tại baseline `ba70f97`. Không triển khai Giai đoạn 7 hoặc AWS.

## Mục lục

- [Quy tắc và phân quyền nhập/bán](#quy-tac-va-phan-quyen)
- [Nghiệp vụ nhập kho, bán hàng, lịch sử kho](#nhap-kho-va-ban-hang)
- [Nghiệm thu nhập → bán → hoàn kho](#nghiem-thu-nhap-ban)
- [Khách hàng và lịch sử mua hàng — 5.1](#khach-hang)
- [Bảo hành và sidebar — 5.2](#bao-hanh)
- [Tinh chỉnh UI/UX trước Giai đoạn 7](#ui-ux-truoc-giai-doan-7)
- [Git và bàn giao](#git-va-ban-giao)

<a id="quy-tac-va-phan-quyen"></a>
## Quy tắc và phân quyền nhập/bán

| Chức năng | Admin | Staff |
| --- | --- | --- |
| Admin Dashboard | Có | 403 |
| Business Dashboard/catalog | Có | Có, giữ quyền CRUD đã duyệt |
| Nhập kho: xem/tạo/xác nhận/hủy | Tất cả | Không |
| Đơn bán: xem/tạo/xác nhận | Tất cả | Chỉ đơn mình tạo |
| Hủy đơn draft | Tất cả | Chỉ đơn mình tạo |
| Hủy đơn completed | Có | Không |
| Lịch sử kho | Tất cả | Movement từ đơn mình, kể cả hoàn hàng do Admin |
| Sửa/xóa movement hoặc xóa giao dịch | Không có route | Không có route |

Đặc tả cho phép Staff nhập **nếu được cấp quyền**; schema role hiện tại chưa cấp
quyền đó. Scope backend áp dụng trước pagination; service kiểm tra lại actor,
role, ownership và trạng thái trước khi ghi. Không mở quyền quản trị cho Staff.

| Từ | Thao tác | Đến | Ảnh hưởng tồn kho |
| --- | --- | --- | --- |
| — | Tạo | draft | Không đổi, không giữ chỗ; snapshot giá và tổng backend |
| draft | Xác nhận | completed | Nhập +quantity, bán −quantity |
| draft | Hủy | cancelled | Không đổi |
| completed | Hủy (Admin) | cancelled | Đảo lượng đúng một lần |
| completed | Xác nhận lại | Từ chối | Không đổi |
| cancelled | Xử lý lại | Từ chối | Không đổi |

Không sửa dòng, xóa cứng giao dịch hoặc sửa tồn trực tiếp trong form sản phẩm.
Hủy nhập completed bị chặn nếu bất kỳ dòng nào thiếu kho. Sau 5.2, hủy đơn bán
completed còn bị chặn khi có phiếu bảo hành chưa trả khách.

<a id="nhap-kho-va-ban-hang"></a>
## Nhập kho, bán hàng và lịch sử kho

### Module nhập kho

Admin tìm mã, lọc supplier/trạng thái/ngày, phân trang 10 dòng. Tạo draft với
supplier active và 1–50 dòng product active; tìm SKU/tên tối đa 50 lựa chọn,
thêm/xóa dòng JS, không lặp sản phẩm. Backend kiểm tra quantity/unit_cost,
tính line_total/tổng bằng Decimal; draft không tăng kho.

Complete tạo purchase_in và audit, tăng kho cùng transaction. Hủy completed
dùng adjustment delta âm/reference purchase_receipt, có lý do; chỉ thực hiện
khi đủ tồn toàn bộ dòng. Chặn hoàn thành/hủy lặp. Unit_cost là snapshot, không
tự cập nhật purchase_price catalog.

### Module bán hàng

Admin xem toàn bộ, Staff chỉ đơn của mình. Danh sách tìm mã/tên khách, lọc
trạng thái/ngày/phân trang. Form nhiều dòng, giá/tồn tham khảo; backend đọc
selling_price từ MySQL để snapshot unit_price, bỏ qua giá/tổng frontend.
Tên khách bắt buộc; phone/email/address tùy chọn đối với vãng lai.

Draft không trừ/giữ chỗ kho. Complete kiểm tra stock sau khóa, tạo sale_out;
thiếu kho bị từ chối. Hủy completed chỉ Admin, sale_return hoàn đúng một lần.
Staff hủy draft của mình. Tích hợp hồ sơ khách xem phần5.1; snapshot bảo hành
xem phần5.2.

### Lịch sử, transaction và chống đồng thời

Lịch sử chỉ đọc, tìm SKU/tên, lọc loại và phân trang20 dòng, liên kết product/
giao dịch theo quyền. Không route chỉnh/xóa movement, không hard delete phiếu.

Mỗi thao tác ghi có Session riêng + begin/commit; auth/render session không sở
hữu transaction nghiệp vụ. Lock document trước, product theo ID tăng dần sau;
kiểm tra state/stock sau giành khóa. Stock/document/movement/audit cùng commit,
lỗi rollback toàn bộ. Deadlock/timeout trả lỗi an toàn, không retry mù; thông báo
hướng người dùng kiểm tra trạng thái trước khi thử lại.

Signed create ticket gắn actor/module/code, hạn2 giờ; UNIQUE code chống submit
cùng form. POST/redirect/GET/loading hỗ trợ UX; row lock/state mới là bảo vệ
chính cho confirm/cancel. Hai form khác nhau là hai giao dịch.

Tiền dùng MySQL DECIMAL(14,2), Python Decimal; JS BigInt cents chỉ preview.
Không float/làm tròn phần lẻ sai. Từng dòng/tổng tối đa999999999999.99; stock
unsigned INT, movement signed INT, không để tồn âm.

Dashboard Giai đoạn6 giữ query KPI/chart/cảnh báo/recent; giao dịch thay stock/
updated_at nên refresh phản ánh dữ liệu thật. Test nhập+5/bán−4/hoàn bán/hủy
nhập xác minh low_stock/inventory_value trở về baseline. Giá trị kho Admin-only,
ước tính theo purchase_price catalog, không phải giá vốn hay lợi nhuận. Chưa
thêm báo cáo doanh thu; link đơn bán thay trạng thái chưa triển khai.

<a id="nghiem-thu-nhap-ban"></a>
## Nghiệm thu nhập → bán → hoàn kho

Bài `test_acceptance_purchase_sale_return_ledger` kiểm tra tồn và toàn bộ delta
sau từng thao tác trên MySQL8 Docker test riêng:

| Thao tác | Tồn | Delta đã ghi |
| --- | ---: | --- |
| Tạo nhập draft5 | 0 | Chưa có |
| Xác nhận nhập | 5 | +5 |
| Tạo bán draft4 | 5 | +5 |
| Xác nhận bán | 1 | +5, −4 |
| Hủy nhập khi thiếu tồn | 1 | Không thêm movement, phiếu vẫn completed |
| Hủy đơn bán completed | 5 | +5, −4, +4 |
| Hủy nhập completed | 0 | +5, −4, +4, −5 |
| Hủy lại các giao dịch | 0 | Từ chối, không thêm movement |

Movement tương ứng purchase_in, sale_out, sale_return, adjustment.

### Kiểm thử Giai đoạn5

- Lượt triển khai: **225 passed /57.54s** (165 regression +60 mới); sau sửa
  thông báo lỗi DB, 5 ca rollback chạy riêng đạt1.75s.
- Nghiệm thu cuối: 225 regression đạt52.24s +1 ca ledger riêng, **226 bài đạt**.
- 5 tình huống service/connection cạnh tranh: oversell, cùng đơn bán, cùng phiếu
  nhập, hủy bán, hủy nhập; mỗi cặp1 thành công/1 từ chối.
- Hai HTTP request test client bán4 cùng stock5:303/409, tồn cuối1. Không SQLite/
  mock row lock. Lỗi sau flush rollback header/items/stock/movement/audit.
- Decimal0/0.01/giá lớn, invalid/overflow, inactive actor/product/supplier, ticket,
  CSRF, scope Staff và Dashboard đạt.
- Browser6 tổ hợp Admin/Staff ×1440×1000/834×1112/390×844; đối chiếu số tiền/
  stock sau từng bước, nhiều dòng/modal/thiếu kho/quyền và no-JS draft đạt.
- Dashboard6 tổ hợp +2 chart fallback +2 no-JS; workspace6; catalog6/18 CRUD/
  72 POST loading; filter/paging/profile18 và no-JS precision/validation đạt.
  Staff11 đơn phân trang10+1 không lộ đơn ngoài owner.
- Runner giữ assertion, đóng snapshot REPEATABLE READ khi cần quan sát commit
  từ service riêng, chờ navigation/empty state đúng. Suite chạy chồng từng gây
  lệch KPI/429; chạy lại tuần tự đạt, không nới limiter hoặc sửa KPI để vượt test.

### File Giai đoạn5

| Nhóm | File chính |
| --- | --- |
| Services | app/services/{inventory_service,transaction_service,purchase_service,sales_service}.py |
| Routes/forms | app/purchases/{__init__,forms,routes,views}.py; app/sales/{__init__,routes}.py; app/inventory/{__init__,routes}.py |
| UI | app/templates/transactions/{base,index,form,detail,movements}.html; app/static/css/transactions.css; app/static/js/transactions.js |
| Tích hợp | app/__init__.py; app/templates/layouts/staff.html; app/templates/dashboard/business.html |
| Kiểm thử | tests/{test_inventory,test_transactions,test_auth,test_dashboard}.py; scripts/{verify_inventory_ui,verify_ui,verify_catalog_ui,verify_catalog_polish}.py |
| Tài liệu | INVENTORY, AUTHENTICATION, ARCHITECTURE, DECISIONS, DASHBOARD, STAGE_6_REPORT; README; .gitignore |

Nghiệp vụ gốc không cần migration/models/dependency/Docker Compose mới. 40 file
lúc triển khai, 41 file ở checkpoint nghiệm thu có thêm ca ledger. Baseline12
bảng demo khớp count/SHA-256, gồm stage1_probe/account/audit; không seed, sửa
tài khoản, chạy migration demo hoặc xóa volume. Revision khi đó db55d828848e.
Snapshot chỉ đọc stage5-before.json và stage5-acceptance-before.json nằm local/
ignored. Web/db/nginx healthy, check-db và nginx config/reload đạt.

Hướng dẫn dùng và chạy lại: [INVENTORY.md](INVENTORY.md).

<a id="khach-hang"></a>
## Khách hàng và lịch sử mua hàng — 5.1

### Chức năng, snapshot và quyền

- Danh sách/tìm tên-phone-email, lọc active/inactive, phân trang10; thêm/xem/sửa,
  kích hoạt/vô hiệu hóa, không hard delete.
- Chuẩn hóa số VN về+84; UNIQUE cả inactive. Số trùng báo rõ/link hồ sơ khi
  xác định được; không tự gộp hoặc tự chọn customer_id. Người dùng chung số có
  thể lập đơn vãng lai.
- Form đơn cho vãng lai, chủ động chọn khách active hoặc inline tạo mới. Search
  gợi ý tối đa20 hồ sơ, xem lịch sử tab khác; backend đọc lại hồ sơ DB, snapshot
  liên hệ và bỏ qua dữ liệu tự điền khi chọn existing.
- Tạo customer+draft/items/audit cùng transaction; lỗi rollback cả khách mới.
  Sửa hồ sơ không đổi snapshot đơn cũ; đơn cũ NULL customer_id không tự liên kết.
- KPI completed count/spent/latest order_date; lịch sử10 đơn/trang và tổng hợp
  sản phẩm completed10 dòng/trang, quantity/unit_price/line_total snapshot.
  Draft/cancelled/vãng lai không vào chi tiêu.
- Admin quản lý hồ sơ/xem mọi trạng thái. Staff chỉ projection completed toàn
  cửa hàng, không notes/audit, không link mở đơn người khác; route đơn đó404.
  Profile new/edit/status độc lập403 cho Staff; tạo khách qua luồng lập đơn.
- Audit customer không ghi giá trị PII; log Nginx bỏ query/referrer để bảo vệ
  từ khóa liên hệ, không nới CSP/script/style.

### Migration và an toàn demo

`db55d828848e → c051_customers`: bảng customers và sales_orders.customer_id
nullable, FK RESTRICT, UNIQUE phone/indexes;11 bảng nghiệp vụ/14FK. Không
backfill/sửa snapshot/state/tiền/tồn đơn cũ.

`verify_customer_migration.py` kiểm tra migrate rỗng và schema cũ có draft/
completed/cancelled, so tất cả cột cũ và probe; customer_id đềuNULL. Không
reset/drop schema/volume.

Tạm stop Nginx chặn ghi UI, giữ web/db; fingerprint12 bảng khớp baseline.
Backup single-transaction không DROP TABLE:
`.docker-local/backups/stage51-20261010T093922Z-21cb76.sql`, manifest SHA-256
cùng tên.json; restore schema mới db-test,12 bảng khớp. Không in dump/password/
hash; backup ignored.

Sau kiểm chứng backup, chạy db upgrade một lần, recreate web/mở Nginx;
`verify_customer_demo_integrity.py` so cột/bảng gốc đạt. db check không có
upgrade operations; login200/services healthy. Snapshot stage51-after.json:
13 bảng tổng,37 products,6 categories,6 suppliers,1 user,7 audit,1 probe,
customers/giao dịch rỗng. Không seed/tạo giao dịch demo.

MySQL DDL có metadata lock và không rollback như DML. Downgrade phá dữ liệu
customers/link bị chặn; rollback app Stage5 có thể giữ schema cộng thêm,
recovery/forward fix phải rà soát riêng.

### Kiểm thử 5.1

- Regression đầu226 bài đạt55.97s; bộ khách ban đầu25 bài, sau đó258 đạt60.90s.
- Bản cuối **260/260 /64.29s**:226 regression +34 khách hàng; chạy lại chốt
  baseline **260/260 /62.05s**.
- Multiple orders, phone, snapshot, completed totals, duplicate/inactive,
  CSRF/anonymous/permissions/pagination/rollback; hai request cùng phone và gửi
  lại order_code với phone khác phải rollback khách vừa chèn đều đạt.
- Migration empty/legacy, restore backup MySQL thật đạt.
- Browser khách hàng6 tổ hợp; tìm phone/lịch sử/KPI, quyền/auto-fill, tạo/confirm,
  inline create, duplicate409, vãng laiNULL, Admin edit/deactivate và snapshot
  cũ bất biến; không pageerror.
- Regression nhập/bán6+no-JS; Dashboard6+2 fallback+2 no-JS; workspace6;
  catalog6/18 CRUD/72 POST và filter/paging/profile18+no-JS đều đạt.
  Compileall/diff --check/secrets scan đạt; không sửa catalog để né timing runner.

42 file mới/sửa lúc bàn giao; context macro, query string POST và fixture tên
trùng trong runner đã sửa/chạy lại đạt. Mọi bảng demo sau nâng cấp vẫn khớp
fingerprint, không reset data hoặc đổi tài khoản.

### File 5.1 và minh chứng

Mới: app/customers/{__init__,forms,routes}.py; app/models/customer.py;
app/services/customer_service.py; templates customers/{base,index,form,detail,
macros,order_picker}.html; static/css/customers.css, static/js/customers.js;
migrations/versions/c051_customers.py; tests/test_customers.py; scripts/
verify_customers_ui.py, verify_customer_migration.py, backup_before_customers.py,
verify_customer_demo_integrity.py; docs/CUSTOMERS.md.

Sửa: app/__init__.py, models/{__init__,sale}.py, purchases/{forms,views}.py,
services/transaction_service.py, layouts/staff.html, transactions/{base,form}.html,
nginx/default.conf, .gitignore, README, tests/test_database.py, scripts/
{verify_ui,verify_catalog_ui,export_database_schema}.py và docs kiến trúc/auth/
database/schema/decisions.

[Hồ sơ desktop](screenshots/stage51-admin-desktop-profile.png) ·
[Hồ sơ mobile](screenshots/stage51-admin-mobile-profile.png).
Ảnh là dữ liệu test riêng. Hướng dẫn: [CUSTOMERS.md](CUSTOMERS.md).

Giới hạn: định dạng VN, chưa OTP/xác minh nhà mạng/khách quốc tế; không merge,
gán lại đơn cũ/bulk import/export/điểm/giảm giá/xếp hạng/voucher. No-JS có20 hồ
sơ đầu hoặc chọn từ profile, search gợi ý cầnJS. Lần mua gần nhất dùng
order_date, chưa completed_at. Tên/SKU vẫn catalog hiện tại, giá là snapshot.

<a id="bao-hanh"></a>
## Bảo hành và sidebar — 5.2

### Chính sách, thiết bị và xử lý

- Chính sách sản phẩm Admin-only, mặc định tắt; bật yêu cầu1–120 tháng/ghi chú.
  Chụp snapshot khi tạo draft bán, completed_at khi hoàn tất; kích hoạt ngày
  bắt đầu/hết hạn theo VN. Sửa catalog không đổi chính sách/đơn cũ.
- Tra cứu completed chưa hủy theo khách/phone/đơn/SKU/serial-IMEI. Đơn cũ thiếu
  snapshot cần Admin xác minh căn cứ, không tự suy đoán bảo hành.
- Thiết bị theo dòng bán+số thứ tự; serial tùy chọn, UNIQUE canonical uppercase
  toàn hệ thống khi có; không tự gắn máy theo tên. Không mở nhiều phiếu đồng thời
  cho một thiết bị.
- Danh sách10 dòng/trang, tìm/lọc trạng thái, tiếp nhận/chi tiết/phân công/xử lý,
  lỗi khách báo/kết quả kiểm tra/lý do từ chối/ngày nhận-hẹn-hoàn tất-trả và50
  event gần nhất chỉ đọc.
- received→processing→completed→returned; received/processing→rejected→returned.
  Không bỏ bước/gửi lặp/mở lại/xóa cứng. Chấp nhận cần xác nhận điều kiện thực tế,
  còn hạn không mặc định miễn phí.
- Không đổi tồn kho từ bảo hành. Chặn hủy đơn completed khi có phiếu chưa trả;
  đóng hết phiếu thì quy tắc đảo kho Stage5 áp dụng.

Admin quản lý tất cả; Staff tra cứu completed toàn cửa hàng ở mức tư vấn, không
notes/audit/địa chỉ/email/tổng tiền, không link mở đơn người khác. Staff chỉ
xem/xử lý phiếu mình tạo hoặc được giao; ngoài scope404, phân công/xác minh/
chính sách chỉ Admin ở backend. Giữ CSRF/session/limiter/CSP; audit không sao
chép lỗi/ghi chú/serial/liên hệ.

Safe log Nginx đặt tại server tránh kế thừa combined; Gunicorn dùng PATH_INFO
thay RAW_URI, bỏ query/referrer. Request kiểm chứng privacy qua proxy/app đạt.

### Sidebar

Nhóm Tổng quan; Đơn hàng (Tạo đơn bán/Danh sách/Khách hàng); Kho hàng (Sản phẩm/
Danh mục/Nhà cung cấp/Nhập hàng/Lịch sử nhập-xuất); Hậu mãi (Bảo hành/Tra cứu);
Tài khoản (Thông tin cá nhân). Click/Enter/Space mở-thu gọn; nhóm route hiện tại
tự mở, active state rõ. Giữ collapse/offcanvas và hai workspace riêng; mục chỉ
hiện theo quyền, không dựng nút giả.

### Schema, transaction và concurrency

`c051_customers → w052_warranty → w052_guards`;15 bảng nghiệp vụ/23FK.
Thêm3 cột products, sales_orders.completed_at nullable và4 bảng:
warranty_coverages, warranty_devices, warranty_tickets, warranty_events.

Devices tách riêng để UNIQUE serial và (coverage_id,unit_index), chỉ tạo khi
tiếp nhận, không sinh theo toàn bộ quantity. open_device_key generated STORED
+UNIQUE chặn phiếu mở trùng tại MySQL, returned trảNULL. Guards siết CHECK/NULL
vì MySQL chấp nhận UNKNOWN.

Session ghi riêng/transaction nguyên tử; lock sales_order→coverage→device→ticket.
Tiếp nhận/xử lý/cancel cạnh tranh cùng order lock; UNIQUE bảo vệ serial giữa
đơn. Signed creation code gắn actor/item, hạn2 giờ, độc lậpCSRF. Kiểm tra state
sau khóa và expected_status, rollback device/ticket/events/audit toàn bộ;
không retry mù deadlock/timeout.

Chi tiết routes/quy tắc/ERD: [WARRANTY.md](WARRANTY.md),
[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

### Kiểm thử 5.2

- Bản cuối **298/298 /90.36s**:260 regression+38 bảo hành.
- Snapshot draft/completion, inactive, valid/expired/off, cuối tháng/năm nhuận,
  lifecycle/reason/state, serial/trùng máy, MySQL UNIQUE/CHECK NULL, concurrency
  cùng máy/serial giữa đơn, xử lý cùng phiếu, tiếp nhận cạnh tranh hủy đơn;
  rollback/audit/CSRF/permission/double-submit đạt.
- Migration empty/legacy có khách/đơn mọi trạng thái/items/movement/probe:
  mọi cột/bảng gốc khớp fingerprint, không backfill ngày/policy.
  compare_metadata không có chênh lệch; chạy lại migration5.1 riêng cũng đạt.
- Browser6 tổ hợp Admin/Staff ×3 viewport+no-JS navigation; Admin phân công,
  xác minh đơn cũ/từ chối có lý do dù còn hạn; Staff xử lý phiếu được giao,
  vẫn không mở được đơn khác owner. Không pageerror/tràn ngang.
- Regression nhập/bán6+no-JS, khách6, Dashboard6+2 fallback+2 no-JS, workspace6,
  catalog6/18 CRUD/72 POST, filter/paging/profile18+no-JS đều đạt.
- Nginx syntax/access-log privacy request thật, links/compileall/diff --check/
  secrets/generated scan đạt. Runner scope selector chart, chờ no-JS navigation,
  giãn suite tránh429; không bỏ assertion/nới limiter. Fixture Windows thiếu
  ZoneInfo dùng UTC+7; app Docker vẫn Asia/Ho_Chi_Minh.

### Migration demo và file 5.2

Sau backend/browser đạt, build web bản cuối/stop riêng Nginx; backup
single-transaction không DROP TABLE:
`.docker-local/backups/stage52-20261010T111539Z-38b06f.sql` +manifest SHA-256.json.
Restore schema mới db-test,13 bảng trước nâng cấp khớp; không in dump/hash/secret.

Db upgrade một lần qua hai revision tới w052_guards, recreate web/mở Nginx.
12 bảng gốc trừ alembic_version giữ nguyên mọi cột/giá trị/fingerprint.
Không backfill policy/completed_at; db check không có upgrade operations,
check-db/nginx config/reload đạt. Snapshot stage52-after.json:17 bảng tổng,
37 products,6 categories,6 businesses,1 user,7 audit,1 probe; customers/giao
dịch/movements/4 bảng bảo hành rỗng. Login/health200, services healthy; không
seed/tạo tài khoản/đổi mật khẩu/reset/drop schema/volume. Downgrade phá lịch sử
bị chặn; DDL không rollback nhưDML, recovery cần rà soát riêng.

Mới: app/models/warranty.py; services/warranty_service.py;
app/warranties/{__init__,forms,routes}.py; templates/warranties/{base,macros,
index,lookup,form,legacy,detail}.html; static/css/warranties.css;
migrations/versions/{w052_warranty,w052_guards}.py; tests/test_warranties.py;
scripts/verify_{warranties_ui,warranty_migration,warranty_demo,document_links,
access_log_privacy,stage52_regression}.py; docs/WARRANTY.md.

Sửa: app/{__init__,models/__init__,models/product,models/sale}.py;
catalog/{forms,resources}.py; services/{catalog_service,transaction_service}.py;
catalog/{form,fields,detail}.html; layouts/staff.html; static/css/workspace.css,
static/js/app.js; Dockerfile/nginx/.gitignore; tests/test_database.py; export
schema/customer migration/browser regression; README và docs kiến trúc/auth/
database/schema/decisions.

[Tiếp nhận desktop](screenshots/stage52-admin-desktop-intake.png) ·
[Đã trả mobile](screenshots/stage52-admin-mobile-returned.png).
Đã dọn261 ảnh lịch sử/tạm (83 docs+178 regression),23.66MB, giữ4 ảnh đại diện
5.1/5.2 trong Git và sửa link. [Danh mục ảnh](screenshots/README.md).
Không xóa thêm ảnh khi gộp tài liệu.

Giới hạn: serial mới ghi lúc tiếp nhận, chưa quản lý lúc giao bán/xác minh nhà
sản xuất; không tự xác minh máy chỉ cùngSKU. Chưa sửa/gộp định danh/snapshot,
đính kèm ảnh/chứng từ, đổi máy/linh kiện/hoàn tiền/phí/thông báo. Tài chính/kho
phải có quy trình riêng, bảo hành không sửa kho. Chưa tải lớn/thiết bị vật lý/
Safari/Firefox/AWS.

<a id="ui-ux-truoc-giai-doan-7"></a>
## Tinh chỉnh UI/UX trước Giai đoạn 7

Phần này giữ kết quả nghiệm thu kỹ thuật của đợt UI vừa hoàn tất; không phải
thay đổi nghiệp vụ hoặc migration mới.

### Cải thiện

- Chi tiết nhập/bán: mã và badge, tiến trình, hai card liên hệ/thông tin giao
  dịch, bảng sản phẩm, tổng số lượng/tổng tiền nổi bật, vùng thao tác cuối trang.
- Tiến trình đọc trạng thái và mốc thật: sales.completed_at khi có; mốc xác nhận/
  hủy từ audit thao tác hiện có, truy vấn chỉ đọc sau kiểm tra scope giao dịch.
  Không trả nội dung audit, IP hoặc dữ liệu giao dịch ngoài quyền. Query dùng
  index entity_type/entity_id. Không tạo event hoặc bổ sung timestamp vào DB.
- Cancelled draft không có bước completed. Cancelled sau completed chỉ hiển thị
  bước completed khi có căn cứ. Legacy thiếu mốc hiển thị phần đã biết, không
  lấy updated_at làm ngày hoàn tất/hủy, không tự suy đoán lịch sử.
- Modal diễn đạt tăng/giảm kho, hủy draft không đổi kho và đảo kho theo loại
  giao dịch. Giữ POST, CSRF, authorization, loading và fallback không JavaScript.
- Bảo hành: tiến trình tiếp nhận/xử lý/hoàn thành/trả; nhánh từ chối/trả riêng.
  Từ chối ngay không đánh dấu đã xử lý hoặc hoàn thành. Từ chối sau xử lý giữ
  bước xử lý nếu có event thật. Timeline không tạo thêm event; lịch sử vẫn chỉ đọc.
- Thời hạn hôm nay được tách khỏi kết quả xử lý tại ngày nhận. Nhãn/icon/màu
  phân biệt còn hạn/hết hạn/không bảo hành/chưa xác định, giữ trạng thái chưa
  kích hoạt/chưa đến hạn. Không đồng nhất còn hạn với miễn phí.
- Liên kết hồ sơ khách khi có customer_id, sản phẩm và đơn bán theo quyền hiện
  hành. Staff nhận bảo hành từ đơn của người khác vẫn chỉ thấy mã đơn bằng chữ.
- CSS bổ sung dùng navy/xanh dương, card và typography hiện có, tiến trình hai
  cột trên mobile, tổng tiền dễ đọc, nút wrap và bảng cuộn trong vùng riêng.
  Icon trang trí aria-hidden; modal có tên/mô tả, focus và bàn phím giữ Bootstrap.
- Cài đặt chỉ có [tài liệu đề xuất](SYSTEM_SETTINGS_PROPOSAL.md); chưa có route,
  bảng, form Lưu hoặc chức năng giả. Không sửa theme/sidebar/workspace chung.

### Kiểm thử

Bản cuối **323/323 backend đạt 92.53s**, gồm 298 regression và 25 bài bổ sung
cho tiến trình, nhánh trạng thái, policy, liên kết/phân quyền/CSRF và legacy thiếu
mốc thao tác. Có kiểm tra không dùng audit của entity khác và không lộ nội dung
audit. Không dùng dữ liệu demo cho fixture.

Browser trên bản cuối đạt 6 tổ hợp Admin/Staff × 1440×1000, 834×1112, 390×844:
draft/completed/cancelled trước và sau hoàn thành, 7 nhánh trạng thái bảo hành,
4 tình trạng chính sách; kiểm tra URL thật, Staff 403/404, CSRF, modal Enter/
Escape/focus, loading submit và không tràn ngang. Không có pageerror hoặc lỗi
tải tài nguyên trong bộ kiểm tra chi tiết mới.

Cả 7 bộ browser regression chạy tuần tự đều đạt trên MySQL test riêng:

| Bộ kiểm tra | Kết quả |
| --- | --- |
| Bảo hành | 6 tổ hợp, bàn phím/menu/tra cứu/tiếp nhận/xử lý/phân quyền và no-JS; 88.0s |
| Nhập kho/bán hàng | 6 tổ hợp, draft/complete/cancel, số tiền, tồn kho, phân quyền và no-JS draft; 97.5s |
| Khách hàng | 6 tổ hợp, lịch sử, snapshot, inline create, duplicate và vãng lai; 89.5s |
| Dashboard | 6 tổ hợp, KPI/chart/bảng thật, 2 fallback lỗi script, 2 no-JS; 18.6s |
| Workspace | Admin/Staff trên 3 viewport, điều hướng và phân quyền; 55.9s |
| Catalog CRUD | 6 tổ hợp, 18 chu trình CRUD và 72 kiểm tra POST/loading; 86.6s |
| Catalog polish | 18 luồng tìm/lọc/phân trang/profile, no-JS CRUD/precision/validation; 44.1s |

Compileall, `git diff --check`, scan secrets/file generated Git-visible đều đạt.
Kiểm tra 94 liên kết file/ảnh nội bộ trong tài liệu đạt. Không staged file nào;
HEAD giữ nguyên baseline, tổng cộng 16 file mới/sửa trong working tree.

Lỗi runner đã sửa: f-string cần escape dict fixture; quan sát DOM trong request
navigation bị chặn gây deadlock, chuyển sang đọc trạng thái tại sự kiện submit;
Escape cần chờ modal Bootstrap nhận focus. Không đổi ứng dụng hoặc bỏ assertion
để xử lý các lỗi runner này; các luồng bản cuối sau sửa đã đạt.

### Bảo vệ dữ liệu và runtime

Trước thay đổi lưu fingerprint/count toàn bộ 17 bảng vào
`.docker-local/prestage7-before.json`, chỉ đọc. Không tạo/chạy migration demo,
seed hoặc sửa tài khoản/secrets. Không xóa schema, database hoặc Docker volume.
Đã cập nhật riêng container web từ image mới và reload Nginx. Web/db/nginx đều
healthy; `/login`, `/health`, stylesheet mới trả HTTP 200, `check-db` kết nối
MySQL thành công. Revision giữ nguyên `w052_guards (head)`; chỉ đọc `db current`,
không chạy upgrade. Sau cập nhật, cả 17 bảng vẫn khớp số dòng và SHA-256 với
baseline; tài khoản, đơn hàng, khách hàng và tồn kho demo giữ nguyên.
Các service ui-nginx/ui/db-test được stop sau kiểm thử; schema và volume test
giữ nguyên. Demo web/db/nginx tiếp tục chạy để nghiệm thu.

### File tạo/chỉnh sửa

Tạo mới:

- `app/templates/components/progress.html`, `app/static/css/detail-polish.css`
- `tests/test_detail_ui.py`, `scripts/verify_detail_polish_ui.py`
- `docs/SYSTEM_SETTINGS_PROPOSAL.md`, báo cáo này.

Chỉnh sửa:

- `app/purchases/views.py`: context timestamp chỉ đọc, scope giữ nguyên.
- `app/templates/transactions/{base,detail}.html`
- `app/templates/warranties/{base,detail,macros}.html`
- `scripts/{verify_catalog_ui,verify_ui}.py`: tùy chọn tắt chụp ảnh regression.
- `.gitignore`, `README.md`.

Không thay services nghiệp vụ, models, forms, migrations, auth hoặc cấu hình Docker.

### Minh chứng giao diện

Đúng 4 ảnh mới cho đợt này, dữ liệu test riêng có nhãn, giữ local/ignored.
Các bộ regression đặt TECHFLOW_CAPTURE_SCREENSHOTS=0 để không sinh thêm ảnh.
Bốn ảnh minh chứng đã version của các giai đoạn trước được giữ nguyên.
Đã xem trực tiếp cả 4 ảnh mới; số liệu và liên hệ trong ảnh là fixture test,
không phải dữ liệu cửa hàng. Bảng sản phẩm trên mobile cuộn ngang trong card.

| Nội dung | Ảnh |
| --- | --- |
| Phiếu nhập completed, desktop Admin | [Xem](screenshots/prestage7-admin-desktop-purchase.png) |
| Đơn bán completed, mobile Staff | [Xem](screenshots/prestage7-staff-mobile-sale.png) |
| Bảo hành từ chối và trả khách, desktop Admin | [Xem](screenshots/prestage7-admin-desktop-warranty-rejected.png) |
| Bảo hành hoàn thành và trả khách, mobile Staff | [Xem](screenshots/prestage7-staff-mobile-warranty-returned.png) |

### Giới hạn

Đơn cũ thiếu timestamp/audit không có đủ thời điểm để tái hiện lịch sử. Không
backfill hoặc suy đoán dữ liệu. Lịch sử bảo hành giữ giới hạn 50 event hiện tại;
mốc xử lý không có trong phần lịch sử được tải sẽ không được tạo bù. Không thêm
thanh toán/giao hàng/công nợ, thư viện chính sách hoặc quản lý cấu hình. Chưa kiểm
thử tải lớn, thiết bị vật lý, Firefox/Safari. Không tạo dữ liệu nghiệp vụ cho demo.

Người dùng đã nghiệm thu phần UI/UX trước Giai đoạn 7 và yêu cầu commit/push.

<a id="ra-soat-cuoi-phieu-nhap"></a>
### Rà soát cuối chi tiết phiếu nhập

Lượt kiểm tra bổ sung sau khi gộp tài liệu, ngày 10/10/2026.
Giữ design system, timeline, card, bảng sản phẩm, mã database/URL và cơ chế sinh mã.

- Thêm nút **Sao chép mã** cho chi tiết nhập/bán. Sao chép nguyên mã, có title,
  accessible label, thông báo live và hỗ trợ Enter/focus. Nếu clipboard bị chặn
  hoặc không hỗ trợ, chọn sẵn mã và hướng dẫn sao chép thủ công. Không JavaScript
  thì nút ẩn, mã đầy đủ vẫn đọc/chọn được; không gọi backend hoặc ghi audit.
- Modal hủy phiếu nhập completed giải thích giảm kho theo toàn bộ lượng đã nhập,
  từng sản phẩm phải đủ tồn để đảo phiếu. Thiếu bất kỳ dòng nào thì từ chối toàn
  bộ, giữ nguyên phiếu/tồn kho. Giữ POST/CSRF/loading/quyền và transaction hiện có.
- Timeline chỉ đọc created_at, completed_at nếu có và timestamp audit đúng entity.
  Không dùng updated_at; đơn thiếu mốc không được suy đoán. Hai sự kiện cùng phút
  hiển thị cùng phút, không tạo giờ khác nhau để phân biệt.
- Banner “DỮ LIỆU KIỂM THỬ RIÊNG — KHÔNG PHẢI DATABASE DEMO” không thuộc template
  ứng dụng. Chỉ helper chụp ảnh test chèn vào DOM sau guard URL test, APP_ENV
  testing và database techflow_test/host db-test. HTTP từ ứng dụng không render
  banner, kể cả khi testing; website demo development/TESTING=False không có banner.

Backend MySQL Docker test riêng: **331/331 passed trong 95.18s**, gồm 323 bài
trước và 8 ca mới: 2 ca nhập/bán có completion/cancel cùng phút, 6 tổ hợp loại
giao dịch × cấu hình testing/development/production không render banner.
Các assertion cũ bổ sung mã sao chép giữ nguyên và nội dung modal đảo kho.

Playwright mới đạt 6 tổ hợp Admin/Staff × desktop/tablet/mobile: clipboard thật,
denied fallback, URL không đổi, Enter/Escape/focus, modal completed, CSRF400,
Staff403 nhập kho/404 đơn ngoài scope, loading và không tràn ngang. No-JS ẩn nút
copy và giữ mã đầy đủ đạt. Các kiểm tra 7 nhánh bảo hành/4 policy cũ vẫn đạt.
Chỉ ghi đè đúng 4 ảnh minh chứng UI hiện có, không sinh thêm bộ ảnh mới.

Chạy lại browser regression nhập/bán đạt đủ 6 tổ hợp Admin/Staff × 3 viewport
và no-JS draft: draft/complete/cancel, số tiền, tồn kho sau mỗi bước, hủy nhập
thiếu tồn nhận409/không đổi kho và quyền thao tác giữ nguyên. Không sinh thêm ảnh.

File chỉnh trong lượt này: app/templates/transactions/detail.html,
app/static/js/transactions.js, app/static/css/detail-polish.css,
tests/test_detail_ui.py, scripts/verify_detail_polish_ui.py và báo cáo này.
Không sửa services/models/migrations/auth hoặc cấu hình Docker.

Đã cập nhật riêng web/reload Nginx, không migration hoặc seed. Sau cập nhật,
17 bảng demo khớp count/SHA-256 với snapshot chỉ đọc trước lượt rà soát trong
.docker-local. Login và script mới HTTP200; APP_ENV=development, TESTING=False.
Compileall, diff --check và 88 liên kết tài liệu đạt. Giới hạn clipboard tùy
quyền trình duyệt; fallback không cam kết tự ghi clipboard. Chưa kiểm tra thiết
bị vật lý/Safari/Firefox; mọi fixture chỉ ở database test riêng.

<a id="git-va-ban-giao"></a>
## Git và bàn giao tổng hợp

| Checkpoint | Commit |
| --- | --- |
| Dashboard6 tích hợp trước phát triển kho | dc0d7be96ab5217bf8cd7c978c8669918cc7b4b6 |
| Nhập kho/bán hàng | c4320cf985f505f3eca4d97f95c3d76e426d9343 |
| Khách hàng | d9e0295c3f1444db85f31807a9b26610ac008532 |
| Bảo hành/sidebar và baseline main | ba70f972aac6cc49772dae5a910b1c893fad8bcc |

Dashboard6 được regression165/49.09s trước commit20 file, fetch main không có
thay đổi bất thường, fast-forward/push thông thường; kho phát triển từ baseline
đó. Baseline5.1 chạy lại260/62.05s trước commit71 file;5.2 phát triển từ tree
sạch. Các lần push/tích hợp main sau đó theo xác nhận của người dùng, không force
hoặc ghi đè lịch sử thành viên khác.

Việc gộp báo cáo lần này chỉ sửa Markdown, bỏ file báo cáo đã được hợp nhất và
cập nhật liên kết. Không chạy lại migration, seed, Docker hoặc test nghiệp vụ;
không sửa code, schema, tài khoản, demo, volume hay screenshot. Kết quả
323/323 và browser phía trên thuộc lượt UI ngay trước khi gộp tài liệu;
331/331 thuộc lượt rà soát phiếu nhập bổ sung sau đó.

Mở http://localhost:8000/login bằng tài khoản hiện có → Không gian kinh doanh.
Nhập hàng chỉ Admin; Staff dùng đơn bán/Khách hàng/Hậu mãi theo scope. Demo chưa
nạp fixture, nên danh sách trống là dữ liệu thật; muốn thử bán cần hàng đã nhập.
Không đặt mật khẩu mặc định, không yêu cầu tạo lại tài khoản.

Hướng dẫn nghiệp vụ: [INVENTORY.md](INVENTORY.md), [CUSTOMERS.md](CUSTOMERS.md),
[WARRANTY.md](WARRANTY.md). Dashboard: [STAGE_6_REPORT.md](STAGE_6_REPORT.md).
Chưa có sửa draft, cấp quyền nhập riêng cho Staff, điều chỉnh kho thủ công, giá
vốn/thuế/hóa đơn/báo cáo doanh thu nâng cao. Chưa kiểm thử tải lớn, thiết bị vật lý,
Safari/Firefox. No-JS nhập/bán hỗ trợ một dòng/50 product đầu; thêm dòng/tìm kiếm
cầnJS. Chưa triển khai Giai đoạn7, hardening/production hoặc AWS.

Phần UI và tài liệu mới đã được người dùng nghiệm thu.
