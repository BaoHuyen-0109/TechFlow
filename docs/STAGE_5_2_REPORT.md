# TechFlow — Giai đoạn 5.2: bảo hành và Sidebar

Ngày 10/10/2026, Asia/Ho_Chi_Minh. Branch `feature/stage-5-2-warranty` từ baseline
5.1 `d9e0295` (`feat: implement customer management and purchase history`).
Chưa commit/push 5.2, chưa merge main, không Giai đoạn 7 hoặc AWS.

## Baseline 5.1 và ảnh cũ

Rà soát Git và chạy 260/260 regression trên MySQL Docker test, 62.05s. Khôi phục
71/98 ảnh tracked bị dọn vì có tài liệu tham chiếu; 27 ảnh không tham chiếu được
ghi nhận xóa trong commit baseline. Giữ 8 ảnh 5.1 local. Báo cáo 5/6 thay 28 liên
kết ảnh local đã mất bằng ghi chú; sửa encoding ghi chú trong đợt bàn giao này.
Commit baseline gồm 71 file mới/sửa/xóa; working tree sạch trước khi tạo branch
5.2. Chưa push hoặc thay đổi lịch sử/merge main.

## Chức năng và nghiệp vụ

- Chính sách sản phẩm Admin-only: mặc định tắt, 1..120 tháng khi bật và ghi chú.
- Chụp chính sách khi tạo draft bán; hoàn tất ghi completed_at và kích hoạt
  ngày bắt đầu/hết hạn theo Việt Nam. Không sửa chính sách/đơn cũ khi sửa catalog.
- Tra cứu completed chưa hủy theo khách, điện thoại, đơn, SKU hoặc serial/IMEI.
  Đơn cũ không bị bỏ qua nhưng cần Admin xác minh căn cứ trước khi nhận bảo hành.
- Thiết bị theo dòng bán + số thứ tự; serial không bắt buộc, UNIQUE canonical
  uppercase toàn hệ thống khi có. Không tự gắn thiết bị theo tên sản phẩm.
- Danh sách phân trang 10 dòng, tìm kiếm/lọc trạng thái, tiếp nhận, chi tiết,
  phân công Admin, xử lý và lịch sử 50 thao tác gần nhất.
- Lưu lỗi khách báo, kết quả kiểm tra, lý do từ chối, ngày nhận/hẹn/hoàn tất/trả.
  Còn hạn không cam kết miễn phí; chấp nhận cần xác nhận điều kiện thực tế.
- State: received → processing → completed → returned; received/processing →
  rejected → returned. Không bỏ bước, gửi lặp, mở lại hoặc xóa cứng lịch sử.
- Không đổi stock từ bảo hành. Chặn hủy đơn completed khi còn phiếu chưa trả;
  sau khi đóng hết phiếu, quy tắc đảo kho Stage 5 tiếp tục áp dụng.

## Quyền

Admin quản lý tất cả. Staff tra cứu completed toàn cửa hàng ở mức cần tư vấn,
không notes/audit/địa chỉ/email/tổng tiền; không link mở đơn người khác. Staff chỉ
xem/xử lý phiếu mình tạo hoặc được phân công. Phiếu ngoài phạm vi trả 404; phân
công/xác minh/chính sách yêu cầu Admin cả backend. CSRF/session/rate limit/CSP
giữ nguyên. Audit không sao chép lỗi, ghi chú, serial hoặc liên hệ.

Sửa privacy access log: cấu hình safe log Nginx chuyển vào server để không kế
thừa thêm combined log mặc định; Gunicorn dùng PATH_INFO thay RAW_URI, không
ghi query/referrer. Script kiểm tra request thật trên test proxy/app đã đạt.

## Schema và đồng thời

`c051_customers` → `w052_warranty` → `w052_guards`, 15 bảng nghiệp vụ / 23 FK.
Thêm 3 cột products, completed_at nullable của sales_orders, 4 bảng:
warranty_coverages, warranty_devices, warranty_tickets, warranty_events.

Thêm bảng devices ngoài thiết kế coverage/ticket/event để đảm bảo UNIQUE serial
và phân biệt từng máy bằng (coverage_id,unit_index). Chỉ tạo khi nhận thiết bị;
không sinh theo toàn bộ quantity. open_device_key generated STORED + UNIQUE chặn
nhiều phiếu mở cùng thiết bị tại MySQL; returned trả key về NULL. Guards làm
chặt CHECK với NULL vì MySQL chấp nhận biểu thức UNKNOWN.

Session ghi riêng, transaction nguyên tử, thứ tự lock sales_order → coverage →
device → ticket. Nhận/xử lý/cancel cạnh tranh cùng order lock. UNIQUE giải quyết
serial tranh giữa các đơn; signed creation code gắn actor/item, hết hạn 2 giờ,
chống double-submit độc lập CSRF. Kiểm tra trạng thái sau khóa và expected_status;
lỗi rollback device/ticket/events/audit. Không retry mù khi timeout/deadlock.

ERD, quy tắc, routes và hướng dẫn nhóm: [WARRANTY.md](WARRANTY.md).
Schema xuất từ models: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## Kiểm thử

- Backend bản cuối: **298/298 đạt trong 90.36s**; 260 regression + 38 bài bảo hành.
- Có kiểm tra snapshot draft/completion, chính sách inactive, còn hạn/hết hạn/
  không bảo hành, cuối tháng/năm nhuận, lifecycle/reason/state, serial/trùng máy,
  MySQL UNIQUE và CHECK NULL, concurrency cùng thiết bị/serial giữa đơn, xử lý
  cùng phiếu và tiếp nhận cạnh tranh hủy đơn; rollback/audit/CSRF/quyền/submit lặp.
- Migration empty và legacy có khách/đơn mọi trạng thái/items/movement/probe:
  fingerprint mọi cột/bảng gốc khớp; không tự cấp bảo hành hoặc backfill ngày.
  Alembic compare_metadata không phát hiện chênh lệch. Chạy lại migration 5.1
  empty/legacy tại revision riêng cũng đạt; không drop/reset schema/volume.
- Browser bảo hành: 6 tổ hợp Admin/Staff × 1440×1000, 834×1112, 390×844 và
  no-JS navigation đạt. Admin phân công qua UI, xác minh đơn cũ rồi từ chối có
  lý do dù còn hạn; Staff xử lý phiếu Admin tạo đã được giao, vẫn không mở được
  đơn bán ngoài phạm vi. Không pageerror hoặc tràn ngang trong các luồng đã chạy.
- Regression nhập/bán: 6 tổ hợp + no-JS draft đạt; khách hàng 6 tổ hợp đạt.
  Dashboard 6 tổ hợp + 2 chart-failure fallback + 2 no-JS đạt.
- Workspace 6 tổ hợp đạt. Catalog 6 tổ hợp, 18 chu trình CRUD và 72 kiểm tra
  POST/loading đạt. Bộ filter/paging/profile đạt 18 luồng, kèm no-JS CRUD,
  độ chính xác DECIMAL và validation. Các suite chạy tuần tự trên db-test.
- Nginx syntax và access-log privacy request thật đạt. Local links và compileall
  đã đạt; rà soát Git-visible chưa thấy secrets/dump/generated file nhạy cảm.

Lỗi runner đã xác định: selector `details` toàn trang trở nên không duy nhất sau
khi thêm menu; đã scope vào chart. No-JS click timing được đổi sang native Enter
và chờ navigation/id route, giữ kiểm tra DECIMAL thực. Các suite đăng nhập quá
sát chạm 429 thật; thêm khoảng chờ, không tắt hoặc bypass rate limiting.
Script browser bổ sung legacy ban đầu thiếu dữ liệu ZoneInfo trên Windows;
đã dùng offset UTC+7 cho ngày fixture tại Việt Nam và chạy lại đạt. Ứng dụng
Docker vẫn dùng Asia/Ho_Chi_Minh; không thay cách tính ngày nghiệp vụ.

## Migration demo

Sau khi backend/browser đạt, đã build web từ bản mã cuối và tạm stop riêng Nginx
để chặn thao tác UI. Backup single-transaction, không DROP TABLE, lưu local/ignored:
`.docker-local/backups/stage52-20261010T111539Z-38b06f.sql` cùng manifest SHA-256
`.json`. Restore vào schema mới trên db-test và so toàn bộ 13 bảng trước nâng
cấp đạt; không in nội dung dump, hash mật khẩu hoặc secrets.

Chạy `docker compose run --rm --no-deps web flask --app wsgi db upgrade` một lần,
qua hai revision tới `w052_guards`, recreate riêng web. Script compare xác nhận
12 bảng gốc (trừ alembic_version) giữ nguyên toàn bộ cột/giá trị/fingerprint.
Không backfill policy hoặc completed_at cho đơn cũ. `db check`: không có upgrade
operations; `check-db` đạt. Mở lại Nginx, nginx -t/reload đạt, ba service healthy.

Snapshot `.docker-local/stage52-after.json`: 17 bảng tổng cộng, 37 products,
6 categories, 6 businesses, 1 user, 7 audit, 1 stage1_probe; customers/giao dịch/
movements/bốn bảng bảo hành đều rỗng. Không seed, tạo tài khoản, đổi mật khẩu,
thay đổi dữ liệu demo hoặc xóa schema/volume. Login và health HTTP 200; route
bảo hành chưa đăng nhập chuyển về login. MySQL DDL không rollback như DML;
downgrade phá lịch sử bị chặn, cần forward fix/recovery được rà soát nếu có sự cố.
Đối chiếu snapshot sau nâng cấp lần cuối đạt cả 17 bảng. Các service test
ui-nginx/ui/db-test đã stop sau kiểm thử, giữ nguyên schema và volume; demo
web/db/nginx tiếp tục hoạt động.

## File

Tạo mới:

- `app/models/warranty.py`, `app/services/warranty_service.py`
- `app/warranties/{__init__,forms,routes}.py`
- `app/templates/warranties/{base,macros,index,lookup,form,legacy,detail}.html`
- `app/static/css/warranties.css`
- `migrations/versions/{w052_warranty,w052_guards}.py`, `tests/test_warranties.py`
- `scripts/verify_{warranties_ui,warranty_migration,warranty_demo,document_links,access_log_privacy,stage52_regression}.py`
- `docs/WARRANTY.md`, báo cáo này.

Chỉnh sửa:

- `app/{__init__,models/__init__,models/product,models/sale}.py`
- `app/catalog/{forms,resources}.py`, `app/services/{catalog_service,transaction_service}.py`
- `app/templates/catalog/{form,fields,detail}.html`, `app/templates/layouts/staff.html`
- `app/static/{css/workspace.css,js/app.js}`, `Dockerfile`, `nginx/default.conf`, `.gitignore`
- `tests/test_database.py`, scripts export schema/customer migration và browser
  regression workspace/catalog/filter/dashboard/inventory.
- README, docs architecture/authentication/database/schema/decisions và ghi chú
  checkpoint 5.1, caption liên kết ảnh của báo cáo 5/6.

## Giao diện

Truy cập http://localhost:8000/login bằng tài khoản hiện có → Không gian kinh
doanh → Hậu mãi. Admin cấu hình bảo hành ở form sản phẩm; đơn bán mới lưu
snapshot và kích hoạt khi completed. Demo chưa có đơn, nên tra cứu hiển thị
empty state thật. Đơn cũ không có snapshot phải được Admin xác minh có căn cứ.

Giữ 2 ảnh đại diện bảo hành: [tiếp nhận desktop](screenshots/stage52-admin-desktop-intake.png) và [phiếu đã trả mobile](screenshots/stage52-admin-mobile-returned.png). Dữ liệu MySQL test riêng được đánh dấu, không phải demo.

Đã dọn ảnh lịch sử và ảnh regression tạm theo yêu cầu mới; docs/screenshots chỉ còn 4 ảnh tổng cộng cho 5.1/5.2. Bốn ảnh được lưu vào Git sau khi rà soát dữ liệu test để liên kết hoạt động trên GitHub; ảnh generated khác vẫn ignored. Xem [danh mục ảnh](screenshots/README.md). Không thay đổi kết quả kiểm thử hoặc chức năng.

## Giới hạn

Serial mới ghi lúc tiếp nhận, chưa quản lý serial lúc giao bán hoặc đối chiếu
nhà sản xuất/IMEI. Không tự xác minh máy chỉ vì cùng SKU; cần nhân viên đối chiếu.
Chưa sửa/gộp định danh, sửa chính sách snapshot, nhập chứng từ/ảnh đính kèm,
đổi máy/linh kiện/hoàn tiền/phí sửa chữa/thông báo khách. Các tác vụ tài chính và
kho tương lai phải có quy trình giao dịch riêng; bảo hành hiện không sửa kho.
Chưa thử tải lớn, thiết bị vật lý, Safari/Firefox. Không triển khai AWS.

Trước lượt dọn ảnh bổ sung có 58 file mới/sửa cho 5.2. Hiện có thêm các thay
đổi tài liệu và xóa ảnh được người dùng yêu cầu; chưa staged/commit/push, HEAD
vẫn d9e0295. Đã xóa 261 ảnh (83 trong docs, 178 ảnh regression tạm), giải phóng
23.66 MB, giữ 4 ảnh đại diện. Cập nhật 8 báo cáo và danh mục ảnh để không có
liên kết hỏng; không thay đổi source ứng dụng, database hoặc volume.
compileall, git diff --check, 87 liên kết file/ảnh tài liệu và scan secrets/
generated files Git-visible đạt. Ảnh chỉ giữ bộ minh chứng cần thiết; các URL
ngoài tài liệu chưa được kiểm tra tự động. Không ghi nhận lỗi chức năng còn
tái hiện trong các luồng đã đạt.

Dừng chờ nghiệm thu trước commit/push 5.2 hoặc Giai đoạn 7.

## Checkpoint Git sau nghiệm thu

Người dùng đã xác nhận commit và push khi kiểm thử đạt. Giữ nguyên kết quả
298/298 backend và browser đã báo cáo; không thay đổi mã ứng dụng sau kiểm thử.
Commit bao gồm bảo hành, Sidebar, tài liệu và dọn ảnh, trên branch
`feature/stage-5-2-warranty`. Push thông thường lên origin, không force push
hoặc merge main; chưa bắt đầu Giai đoạn 7.
