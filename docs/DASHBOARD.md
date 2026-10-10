# Dashboard — Thống kê catalog và tồn kho

Phạm vi Giai đoạn 6 giữa kỳ, dựa trên dữ liệu hiện có; không cần Giai đoạn 5.
Giữ hai workspace: `/admin/dashboard` quản trị hệ thống và `/staff/dashboard`
kinh doanh. Admin mặc định vào quản trị, chọn **Không gian kinh doanh** để xem
đầy đủ thống kê; Staff mặc định vào Business. Không đổi session hoặc role khi
chuyển workspace. Link **Thông tin cá nhân** vẫn tới phần phiên `#session`.

## KPI và phạm vi dữ liệu

| KPI | Công thức/phạm vi | Quyền Dashboard |
| --- | --- | --- |
| Sản phẩm hoạt động | COUNT products WHERE is_active=true | Admin, Staff |
| Danh mục hoạt động | COUNT categories WHERE is_active=true | Admin, Staff |
| Nhà cung cấp hoạt động | COUNT businesses WHERE is_active=true | Admin, Staff |
| Sản phẩm tồn kho thấp | COUNT products WHERE is_active=true AND stock_quantity <= reorder_level | Admin, Staff |
| Giá trị tồn kho ước tính | SUM(stock_quantity × purchase_price), tất cả sản phẩm kể cả inactive | Chỉ Admin |

Giá trị tồn kho vẫn tính hàng còn tồn của sản phẩm ngừng hoạt động vì số hàng
đó vẫn còn trong database. Đây là ước tính theo giá nhập hiện tại, không phải
lợi nhuận hoặc giá vốn kế toán. Toàn bộ phép nhân/SUM ở MySQL DECIMAL, kết quả
là Python Decimal, hiển thị VND với hai chữ số phần lẻ; không qua float/JavaScript.
Catalog rỗng cho count 0, tổng giá trị 0,00 ₫. Dữ liệu giá/stock thiếu hoặc âm
cho giá trị “Chưa thể ước tính”, không thay bằng 0. Schema hiện có đã chặn phần
lớn dữ liệu sai; kiểm tra bổ sung bảo vệ trường hợp import dữ liệu không hợp lệ.

Staff không nhận trường inventory_value, không truy vấn purchase_price trong
service Dashboard. Query string `role=admin`/`include_value=true` không thay
quyền. Điều này chỉ giới hạn thống kê tổng giá trị; quyền CRUD/xem chi tiết
catalog của Giai đoạn 4 vẫn giữ nguyên. Staff vẫn bị chặn route quản trị bằng
decorator backend. Không thêm endpoint JSON hoặc xuất dữ liệu ngoài quyền.

## Biểu đồ và các danh sách

- Sản phẩm theo danh mục: chỉ products active; danh mục inactive vẫn có thể chứa
  sản phẩm active, nên giữ chúng và ghi chú trạng thái danh mục trong bảng.
  Top 8 theo số lượng giảm dần, ID tăng dần khi bằng nhau. Nếu còn nhóm khác,
  cộng số sản phẩm còn lại vào “Danh mục khác”; tổng các cột bằng KPI active.
  Không tạo danh mục giả trong DB. Danh mục không có sản phẩm active không có cột.
- Chart.js **4.5.1**, UMD/MIT lưu trong `app/static/vendor/chartjs` cùng license,
  provenance và SHA-256. Không CDN hoặc mở thêm CSP. Canvas có ARIA label, bảng
  HTML thay thế luôn có trong response. Không JS hoặc thư viện lỗi vẫn đọc bảng;
  không có dữ liệu thì empty state, không vẽ cột 0 giả.
- Cảnh báo: chỉ active và `stock_quantity <= reorder_level`, kể cả 0 <= 0.
  Tối đa 8 dòng, ưu tiên stock thấp nhất rồi tên/ID. Hiển thị số dòng/tổng cảnh
  báo, SKU, tên, danh mục, tồn kho, ngưỡng, trạng thái Hết hàng/Tồn kho thấp.
  Tên sản phẩm liên kết tới chi tiết thật; bảng cuộn ngang trong region riêng.
- Gần đây: tối đa 6 sản phẩm theo GREATEST(created_at,updated_at) giảm dần rồi ID
  giảm dần, gồm inactive vì cả hai role hiện được xem chúng trong catalog.
  Ghi trạng thái, Tạo mới/Cập nhật và timestamp UTC → Asia/Ho_Chi_Minh.
  Không dùng audit/user/giao dịch bán hàng làm nguồn hoạt động này.

## Truy vấn và trạng thái

Mỗi lần GET/Làm mới thực hiện 6 SELECT trong một transaction đọc mới, không
cache/hardcode KPI. Các bảng catalog cùng snapshot mặc định REPEATABLE READ của
MySQL 8 hiện tại. Không ghi database hoặc cập nhật stock/updated_at/audit.
Làm mới là GET thật, có loading từ component form chung. Biểu đồ có trạng thái
dựng/thành công/fallback. Khi truy vấn lỗi, trả HTTP503, thông báo tiếng Việt,
link Thử lại và thông tin phiên; không hiện KPI 0 hoặc SQL/stack trace.

Các FK/category_id và is_active đã có index. Aggregate vẫn cần đọc dữ liệu phù
hợp; so sánh stock với reorder và sort GREATEST timestamp có thể quét/sort bảng.
LIMIT giới hạn kết quả trả về, không bảo đảm không quét bảng. Không thêm index/
migration cho MVP hiện tại; nhóm cần đo EXPLAIN/tải trước khi chọn index cho
dữ liệu lớn. Không tuyên bố đã kiểm thử tải hoặc triển khai production.

## Kiểm thử và bàn giao

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
docker compose -f docker-compose.db-test.yml --profile ui up -d --wait --wait-timeout 120 ui-nginx
docker compose -f docker-compose.db-test.yml exec -T ui-nginx nginx -s reload
.\.venv\Scripts\python.exe scripts/verify_dashboard_ui.py
.\.venv\Scripts\python.exe scripts/verify_ui.py --screenshot-prefix stage6-regression
.\.venv\Scripts\python.exe scripts/verify_catalog_ui.py --screenshot-prefix stage6-catalog
.\.venv\Scripts\python.exe scripts/verify_catalog_polish.py
docker compose -f docker-compose.db-test.yml --profile ui stop ui-nginx ui db-test
```

Chạy tuần tự để không gặp giới hạn POST /login theo IP. Playwright cần môi trường
requirements-ui.txt và Chromium local như README. Các script có guard DB test,
credentials ngẫu nhiên không in log; fixture riêng được dọn trong DB test.
Test rỗng/biên dùng bảng TEMPORARY chỉ trên connection test, không TRUNCATE/xóa
các bảng gốc. Trong fixture, DROP TEMPORARY chỉ dọn các bảng tạm đó.

Giới hạn/chờ nhóm sau giữa kỳ: nhập/bán và transaction cập nhật tồn kho, báo cáo
doanh thu từ đơn completed, top bán chạy, khoảng ngày báo cáo, giá vốn/hoàn hàng,
phân trang toàn bộ cảnh báo nếu cần, tối ưu index theo số liệu tải, AWS/production.
Không có dữ liệu doanh thu/đơn bán giả hoặc nút nghiệp vụ chưa hoạt động.
