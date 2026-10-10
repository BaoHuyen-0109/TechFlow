# TechFlow — Giai đoạn 5: nhập kho, bán hàng và tồn kho

Ngày 10/10/2026. Branch `feature/stage-5-inventory-sales`.
**Người dùng đã duyệt commit/push branch sau nghiệm thu cuối; không merge main.**

## Git baseline

- Kiểm tra branch/status/diff và diff --check; rà soát Git-visible files với các
  giá trị secrets local trong bộ nhớ, không in chúng. .env/.venv/cache/database/
  volumes/file tạm/screenshot sinh tự động không vào commit.
- Chạy lại Giai đoạn 6: 165 backend tests đạt 49.09s; Dashboard 6 role/viewport
  flows, 2 chặn chart và 2 no-JS đạt.
- Commit 20 file Giai đoạn 6: `dc0d7be96ab5217bf8cd7c978c8669918cc7b4b6`, message
  `feat: implement stage 6 business dashboard and analytics`.
- Fetch origin: main trên remote vẫn `a4529f7`, không có thay đổi bất thường.
- Main fast-forward tới dc0d7be, push origin main thông thường. `ls-remote`, local
  main và origin/main cùng hash dc0d7be. Không force/reset/rebase lịch sử chung.
- Tạo branch Giai đoạn 5 từ main mới này. Những thay đổi dưới đây chưa staged.

## Chức năng hoạt động

### Nhập kho

Admin xem danh sách, tìm theo mã, lọc supplier/trạng thái/ngày và phân trang 10
dòng. Tạo phiếu draft với supplier active, 1–50 dòng product active; có tìm SKU/
tên tối đa 50 lựa chọn và thêm/xóa dòng JS. Không lặp sản phẩm. Backend kiểm tra
số lượng/đơn giá, tự tính line_total và tổng bằng Decimal. Draft không tăng kho.

Chi tiết có đơn giá snapshot/tổng số lượng/tổng tiền/trạng thái và modal xác nhận.
Complete tăng kho, purchase_in và audit trong một transaction. Chặn xác nhận
lần hai. Hủy draft không đổi kho; hủy completed đảo lượng bằng adjustment delta
âm/reference purchase_receipt, reason rõ ràng, chỉ khi đủ kho cho toàn bộ dòng.

### Bán hàng

Admin xem tất cả; Staff chỉ xem/tạo đơn của mình. Danh sách tìm mã/tên khách,
lọc trạng thái/ngày/phân trang. Form có tên khách bắt buộc và phone/email/address
tùy chọn, giá/tồn kho tham khảo, nhiều dòng. Backend lấy selling_price tại lúc
tạo, snapshot unit_price, bỏ qua giá/tổng frontend và kiểm tra tồn kho.

Draft không trừ hoặc giữ chỗ hàng. Complete khóa và kiểm tra stock hiện tại,
giảm kho và tạo sale_out/audit nguyên tử. Hủy completed chỉ Admin, hoàn hàng
sale_return đúng một lần; Staff được hủy draft của mình. Không sửa/xóa phiếu.

### Lịch sử và quyền

Lịch sử kho chỉ đọc, tìm SKU/tên, lọc loại, phân trang 20 dòng, link tới product/
giao dịch. Admin xem tất cả; Staff chỉ movement tham chiếu đơn của mình, kể cả
movement hoàn hàng do Admin thực hiện. Không có route sửa/xóa movement.

Staff không có quyền nhập kho, xem đơn người khác hoặc quản trị hệ thống. Builder
scope danh sách/detail/history ở backend trước pagination; service kiểm tra lại
actor/role/ownership/state khi ghi. Giữ hai Dashboard, Flask-Login, session,
CSRF, rate limiting, security headers và quyền CRUD catalog hiện tại.

Ma trận chi tiết: [STAGE_5_PLAN.md](STAGE_5_PLAN.md).

## Transaction và chống đồng thời

Mỗi lần ghi dùng Session riêng + begin/commit; auth/render session không sở hữu
transaction đó. Xác nhận/hủy khóa document trước, product theo ID tăng dần sau;
kiểm tra state/stock sau khi giành khóa. Các thao tác cập nhật stock, document,
movement và audit cùng transaction, lỗi rollback toàn bộ. Database deadlock/
timeout được rollback và trả thông báo an toàn, không retry mù thao tác ghi.

Signed create ticket gắn actor/module/code, hạn 2 giờ + UNIQUE code chặn tạo trùng
từ cùng form. POST/redirect/GET/loading hỗ trợ UX; row lock/state mới là bảo vệ
chính cho confirm/cancel. Hai form mới khác nhau là hai giao dịch riêng.

Không float: MySQL DECIMAL(14,2), Python Decimal, JS BigInt cents cho preview.
Kiểm tra từng dòng và tổng không vượt 999999999999.99, không làm tròn phần lẻ
không hợp lệ. Stock giới hạn unsigned INT, movement signed INT. Stock không âm.

## Dashboard

Giữ toàn bộ query KPI/chart/cảnh báo/recent Giai đoạn 6, cùng quyền Staff/Admin.
Transaction thay stock/updated_at nên Làm mới phản ánh dữ liệu thực. Đã thêm test
nhập +5, bán -4, hoàn bán và hủy nhập: low_stock/inventory_value đúng và trở về
baseline sau đảo kho. Tổng giá trị kho vẫn Admin-only và ước tính theo giá mua
catalog, không tự đổi purchase_price theo phiếu nhập. Thay nội dung “chưa triển
khai đơn hàng” bằng link đơn bán thật. Chưa thêm báo cáo doanh thu/lợi nhuận.

## Kiểm thử

- Backend Docker/MySQL 8.0.44 test riêng: **225 passed in 57.54s**.
- Sau cập nhật thông báo lỗi DB hướng người dùng kiểm tra trạng thái trước khi
  thử lại, chạy riêng 5 ca rollback trên image mới nhất: **5 passed in 1.75s**.
- Gồm 165 test cũ và 60 test mới: draft không đổi kho; confirm/cancel một lần;
  thiếu kho; nhiều dòng lỗi rollback cả dòng trước; lỗi sau flush SQL rollback
  header/items/stock/movement/audit; Decimal 0/0.01/giá trị lớn; invalid/overflow;
  inactive product/supplier/actor; signed ticket/CSRF; scope Staff và Dashboard.
- 5 kịch bản đồng thời qua service/connection riêng: oversell, cùng đơn bán,
  cùng phiếu nhập, hủy đơn bán, hủy nhập. Mỗi cặp đúng 1 thành công/1 từ chối.
- 2 HTTP request thực trong Flask test client riêng cạnh tranh stock 5, cùng
  bán 4: statuses 303/409, tồn kho cuối 1. Không dùng SQLite hoặc mock row lock.
- Playwright Chromium nghiệp vụ: **6/6** Admin/Staff × desktop/tablet/mobile,
  đối chiếu Decimal và stock thật sau mỗi bước, nhiều dòng/tìm sản phẩm/xóa-thêm
  dòng/modal/thiếu kho/quyền/ảnh; thêm 1 no-JS tạo draft đạt.
- Dashboard regression: 6/6 Admin/Staff × 3 viewport; 2 chart-failure và 2 no-JS đạt.
- Workspace regression: 6/6, login/logout, role, menu và chuyển hai workspace đạt.
- Catalog regression: 6/6, 18 vòng CRUD và 72 POST loading checks đạt; giá lưu
  MySQL được đối chiếu bằng Decimal.
- Filter/paging/profile regression: 18/18 module/role/viewport flows đạt, kèm
  no-JS CRUD/precision/validation. Test Staff mới xác minh 11 đơn chia 10 + 1,
  giữ trạng thái lọc và không lộ đơn người khác.

Lượt đầu test cần đóng snapshot REPEATABLE READ của assertion session để quan
sát transaction vừa commit ở session service riêng. Đã sửa fixture đọc này và
route render lỗi. Email dùng validator tiếng Việt có sẵn thay dependency chưa
cài. Các assertion “đơn hàng chưa khả dụng/menu pending” cũ đã cập nhật đúng
chức năng mới, giữ mọi kiểm tra bảo mật. Runner no-JS tách click và chờ navigation
để tránh timeout đồng bộ trình duyệt. Các luồng nghiệp vụ cuối đã đạt.

## File tạo/chỉnh sửa

Tổng cộng 40 file: 23 mới và 17 chỉnh sửa; không có file staged.

| Nhóm | File |
| --- | --- |
| Services mới | app/services/inventory_service.py, transaction_service.py, purchase_service.py, sales_service.py |
| Routes/forms mới | app/purchases/forms.py, routes.py, views.py; app/sales/routes.py; app/inventory/__init__.py, routes.py |
| UI mới | app/templates/transactions/base.html, index.html, form.html, detail.html, movements.html; app/static/css/transactions.css; app/static/js/transactions.js |
| Đăng ký/điều hướng | app/__init__.py, app/purchases/__init__.py, app/sales/__init__.py, app/templates/layouts/staff.html |
| Dashboard | app/templates/dashboard/business.html (copy/link), không thay service KPI |
| Tests | tests/test_inventory.py, tests/test_transactions.py mới; test_auth.py, test_dashboard.py cập nhật assertions |
| Browser runner | scripts/verify_inventory_ui.py mới; scripts/verify_ui.py thêm hai link thật vào allowlist Staff; scripts/verify_catalog_ui.py chờ empty state bằng Playwright expect; scripts/verify_catalog_polish.py chờ navigation GET trước khi đọc số dòng/URL |
| Tài liệu | docs/STAGE_5_PLAN.md, INVENTORY.md, STAGE_5_REPORT.md mới; README.md, AUTHENTICATION.md, ARCHITECTURE.md, DECISIONS.md, DASHBOARD.md, STAGE_6_REPORT.md cập nhật |
| Ignore | .gitignore: screenshot stage5 giữ local |

Không đổi models, migration, Docker Compose, dependencies, secrets hay seed.
Catalog regression dùng assertion có chờ cho empty state sau GET lọc, tránh đọc
DOM giữa lúc điều hướng. Controls chỉ hoạt động với JavaScript được ẩn khi tắt
JavaScript; form draft một dòng và form xác nhận/hủy native vẫn sử dụng được.

## Screenshot và xem giao diện

Viewport 1440×1000, 834×1112, 390×844, zoom 100%; không chỉnh kích thước toàn hệ
thống theo ảnh thu nhỏ. Đã xem ảnh desktop form nhập, mobile form nhập và tablet
chi tiết đơn bán. Không tràn ngang toàn trang; bảng cuộn trong region riêng.

| Minh chứng | Desktop | Mobile |
| --- | --- | --- |
| Tạo phiếu nhập | [Ảnh](screenshots/stage5-admin-desktop-purchase-form.png) | [Ảnh](screenshots/stage5-admin-mobile-purchase-form.png) |
| Nhập hoàn thành | [Ảnh](screenshots/stage5-admin-desktop-purchase-completed.png) | [Ảnh](screenshots/stage5-admin-mobile-purchase-completed.png) |
| Tạo đơn bán | [Ảnh](screenshots/stage5-admin-desktop-sales-form.png) | [Ảnh](screenshots/stage5-staff-mobile-sales-form.png) |
| Đơn bán hoàn thành | [Ảnh](screenshots/stage5-admin-desktop-sales-completed.png) | [Ảnh](screenshots/stage5-staff-mobile-sales-completed.png) |
| Lịch sử kho | [Ảnh](screenshots/stage5-admin-desktop-movements.png) | [Ảnh](screenshots/stage5-staff-mobile-movements.png) |
| Staff403 | [Ảnh](screenshots/stage5-staff-desktop-admin-forbidden.png) | [Ảnh](screenshots/stage5-staff-mobile-admin-forbidden.png) |

Ảnh/dữ liệu là fixture trong DB test, không phải dữ liệu demo chính. Ảnh sinh tự
động được ignore, giữ local để chọn minh chứng sau nghiệm thu.

Mở http://localhost:8000/login, dùng tài khoản hiện có, vào **Không gian kinh
doanh**. Admin có **Nhập hàng**, **Bán hàng và đơn bán**, **Lịch sử nhập / xuất**.
Không cần tạo lại tài khoản hoặc chạy seed. Demo chính trước bàn giao chưa được
tạo giao dịch; muốn thử luồng bán cần nhập/xác nhận hàng trước.

## Dữ liệu, vận hành và giới hạn

Main đã rebuild riêng web bằng --no-deps, check-db thành công; Alembic vẫn
db55d828848e (head), db check không có upgrade operations, Nginx config/reload đạt.
Không chạy upgrade/seed trên main. Snapshot trước thay đổi ở ignored
.docker-local/stage5-before.json; fingerprint/count cả 12 bảng giữ nguyên trong
các lượt kiểm tra, gồm account, audit, stage1_probe và tất cả giao dịch cũ.

Kiểm tra cuối: cả 12 bảng có row count/SHA-256 giống baseline; web/db/nginx healthy,
login HTTP200. Container test đã dừng bằng stop, mọi volume giữ nguyên. compileall,
diff --check và kiểm tra link tài liệu/ảnh đạt; index rỗng, HEAD vẫn dc0d7be.
Không ghi nhận lỗi chức năng còn tồn tại trong các kịch bản đã kiểm thử.

Chưa kiểm thử tải lớn, Safari/Firefox hoặc thiết bị vật lý. No-JS hỗ trợ tạo một
dòng với 50 product đầu; tìm kiếm/thêm dòng cần JS. Chưa có sửa draft; hủy và tạo
mới. Chưa có cấp quyền nhập kho riêng cho Staff, điều chỉnh kho thủ công, giá
vốn/thuế/hóa đơn, báo cáo doanh thu nâng cao. Tên sản phẩm/supplier không snapshot;
giá và lượng giao dịch có snapshot. Cần giai đoạn riêng để hardening/production/
AWS, không thực hiện các phần đó ở đây.

Lệnh kiểm thử và quy trình dùng: [INVENTORY.md](INVENTORY.md).
## Nghiệm thu cuối trước commit

Người dùng cho phép commit với message
`feat: implement inventory purchasing and sales workflows` và push thông thường
branch `feature/stage-5-inventory-sales`, không merge main, không chuyển giai đoạn.
Kết quả lượt nghiệm thu cuối được ghi ở [STAGE_5_ACCEPTANCE.md](STAGE_5_ACCEPTANCE.md).
