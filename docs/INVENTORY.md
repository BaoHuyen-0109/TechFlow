# Nhập kho, bán hàng và lịch sử kho

## Truy cập và quyền

Đăng nhập tại http://localhost:8000/login bằng tài khoản hiện có, vào **Không gian
kinh doanh**. Các route:

- `/business/purchases`: phiếu nhập, chỉ Admin.
- `/business/sales`: đơn bán; Admin thấy tất cả, Staff chỉ thấy đơn mình tạo.
- `/business/inventory`: lịch sử chỉ đọc; Staff chỉ thấy biến động của đơn mình.
- Mỗi module giao dịch có `/new`, `/<id>`, POST `/<id>/complete`, POST `/<id>/cancel`.
- GET `/business/{purchases|sales}/products?q=...`: tìm tối đa 50 sản phẩm active.

Chi tiết ma trận quyền và state machine: [Quy tắc Giai đoạn 5](STAGE_5_REPORT.md#quy-tac-va-phan-quyen).
Không có quyền nhập kho riêng trong schema hiện tại: Staff chưa được cấp quyền
đó. Chỉ Admin hủy giao dịch completed. Staff có thể hủy đơn draft do mình tạo.
Thay role/account bị vô hiệu hóa có hiệu lực theo loader Flask-Login hiện có;
service kiểm tra lại actor active/role trên connection ghi.

## Luồng sử dụng

1. Tạo phiếu nhập, chọn supplier active và các sản phẩm active. Nhập số lượng,
   đơn giá không âm; tối đa 50 dòng, không lặp sản phẩm. Đơn giá nhập không có
   phân cách hàng nghìn, dấu chấm thập phân; ví dụ `15000.50`.
2. Lưu draft: backend tính tổng bằng Decimal, **chưa cộng kho**.
3. Xem chi tiết, xác nhận bằng modal. Khi thành công, tăng kho và ghi lịch sử.
4. Tạo đơn bán: chọn sản phẩm và khách hàng. Giá hiện tại/tồn kho chỉ tham khảo.
   Backend lấy lại selling_price từ MySQL và snapshot vào unit_price; không tin
   unit_price hoặc tổng do trình duyệt gửi. Bản nháp không giữ chỗ hàng.
5. Xác nhận đơn: khóa và kiểm tra lại tồn kho hiện tại, giảm kho nếu đủ.
6. Admin hủy completed: đơn bán hoàn hàng; phiếu nhập trừ lượng nhập nếu đủ hàng.
   Nếu thiếu bất kỳ sản phẩm nào, toàn bộ thao tác hủy bị rollback.

Không sửa dòng/xóa phiếu, không sửa stock trực tiếp hoặc sửa/xóa movement. Muốn
thay đổi draft hiện tại, hủy và tạo phiếu mới. Phần điều chỉnh kho thủ công ngoài
phạm vi này. Giao dịch giữ đơn giá snapshot nhưng tên/SKU/supplier hiển thị theo
catalog hiện tại; không phải hệ thống hóa đơn pháp lý.

## Transaction và đồng thời

Routes dùng session đọc cho auth/render; service mở `Session(db.engine)` riêng
và `session.begin()` cho một đơn vị ghi nguyên tử. Thành công mới commit; lỗi
ra khỏi context rollback cả header/items/stock/movement/audit. Route đóng snapshot
đọc cũ khi cần render lỗi, tránh đọc trạng thái cũ theo REPEATABLE READ.

Xác nhận/hủy khóa document bằng `SELECT ... FOR UPDATE`, kiểm tra state sau khi
khóa; tiếp đó khóa từng product theo ID tăng dần. Các đơn khác nhau cạnh tranh
product lock và kiểm tra lượng còn lại **sau** khi giành khóa. Request xử lý cùng
phiếu chờ document lock rồi bị từ chối nếu state không còn phù hợp. Tất cả module
kho dùng chung thứ tự này. Deadlock/timeout/DB failure trả lỗi thân thiện, rollback;
người dùng tải lại trạng thái trước khi thử, không retry mù thao tác ghi.

Tạo form nhận ticket ký bằng secret hiện có, gắn actor/module/code, hết hạn sau
2 giờ. Cùng form submit hai lần có cùng mã: UNIQUE DB chặn bản thứ hai. Ticket
không thay CSRF. POST/redirect/GET và loading giảm double-click; backend vẫn chặn
xử lý lặp khi bỏ qua JavaScript. Hai tab mở hai form mới là hai giao dịch khác nhau.

Tiền: DECIMAL(14,2), kiểm tra 0..999999999999.99 và không làm tròn phần lẻ vượt
2 chữ số; từng line và tổng đều phải trong giới hạn. JavaScript preview dùng
BigInt theo cent, không Number/float. Quantity 1..2147483647 để phù hợp signed
movement delta; stock 0..4294967295 theo MySQL unsigned INT. Dữ liệu tràn giới
hạn bị chặn trước commit.

Đảo phiếu nhập dùng movement `adjustment`, reference_type `purchase_receipt`,
delta âm, reason cố định; không cần thay CHECK/schema. Audit không chứa dữ liệu
khách hàng, ghi chú, ticket, password hoặc secrets. Không tự cập nhật giá nhập
catalog thành đơn giá phiếu; cần quy tắc giá vốn/định giá riêng ở tương lai.

## Dashboard

KPI/chart/cảnh báo đọc lại MySQL như Giai đoạn 6. Nhập/xuất/hoàn hàng thay đổi stock
và updated_at nên giá trị kho, cảnh báo và recent tự cập nhật sau Làm mới. Không
thêm tổng doanh thu hoặc lợi nhuận trong đợt này; báo cáo doanh thu nâng cao còn
chưa triển khai. Tổng kho vẫn Admin-only, không thay quyền hai workspace.

## Kiểm thử local

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
docker compose -f docker-compose.db-test.yml --profile ui up -d --wait --wait-timeout 120 ui-nginx
docker compose -f docker-compose.db-test.yml exec -T ui-nginx nginx -s reload
.\.venv\Scripts\python.exe scripts/verify_inventory_ui.py
.\.venv\Scripts\python.exe scripts/verify_dashboard_ui.py
.\.venv\Scripts\python.exe scripts/verify_ui.py --screenshot-prefix stage5-regression
.\.venv\Scripts\python.exe scripts/verify_catalog_ui.py --screenshot-prefix stage5-catalog
.\.venv\Scripts\python.exe scripts/verify_catalog_polish.py
```

Chạy tuần tự, không chạy backend đang ghi test fixtures song song với browser KPI
assertions. Tất cả nghiệp vụ test có guard `techflow_test` trên `db-test`; không
chạy chúng bằng DB demo chính. Lịch sử giao dịch test được giữ lại ở DB test để
kiểm tra; không xóa movement/volume sau kiểm thử. Screenshot `stage5-*` được ignore
và giữ local; cần chọn minh chứng khi nghiệm thu/commit.

Không cần migration mới hoặc seed lại để sử dụng. Không triển khai AWS. Bàn giao
tiếp: cấp quyền nhập kho chi tiết nếu cần, điều chỉnh kho có lý do/phân quyền,
giá vốn, báo cáo doanh thu có khoảng thời gian, hardening/production/AWS theo
giai đoạn riêng. Chưa kiểm thử tải quy mô lớn hoặc thiết bị vật lý.
