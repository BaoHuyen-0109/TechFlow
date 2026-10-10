# TechFlow — Giai đoạn 6 Dashboard & Thống kê giữa kỳ

> Cập nhật baseline 10/10/2026: người dùng đã duyệt commit/tích hợp. Giai đoạn 6
> được commit `dc0d7be96ab5217bf8cd7c978c8669918cc7b4b6`, fast-forward vào main và
> push thông thường; local/remote cùng hash. Nội dung bên dưới giữ snapshot thời
> điểm báo cáo trước nghiệm thu. Giai đoạn 5 phát triển trên branch riêng.

Ngày: 10/10/2026, giờ Việt Nam. Website Docker local đã cập nhật.
**Chưa commit/push; dừng chờ nghiệm thu. Không triển khai Giai đoạn 5/7/8/9 hoặc AWS.**

## Git và phạm vi

Bắt đầu từ `main`, working tree sạch, commit mới nhất `a4529f7d063313ec581cff3e110811b4c455dfab`
đã đồng bộ GitHub. Tạo nhánh `feature/stage-6-dashboard`; không reset hoặc ghi
đè thay đổi người dùng. HEAD vẫn ở commit Giai đoạn 4, index không có file staged.

Đã đọc lại đặc tả chính thức và code hiện tại. Nâng cấp Dashboard kinh doanh
`/staff/dashboard`, giữ layout/sidebar navy, typography và hai workspace riêng.
Admin Dashboard hệ thống `/admin/dashboard` vẫn giữ thông tin tài khoản, phân
quyền và trạng thái kết nối; Admin dùng **Không gian kinh doanh** để xem thống kê
đầy đủ và **Quay về quản trị** để quay lại, giữ nguyên session/role.

## KPI và dữ liệu thật

| Chỉ số | Định nghĩa | Giá trị database chính lúc kiểm tra |
| --- | --- | --- |
| Sản phẩm hoạt động | COUNT products WHERE is_active=true | 37 |
| Danh mục hoạt động | COUNT categories WHERE is_active=true | 6 |
| Nhà cung cấp hoạt động | COUNT businesses WHERE is_active=true | 6 |
| Sản phẩm tồn kho thấp | Active AND stock_quantity <= reorder_level | 37 |
| Giá trị tồn kho ước tính | SUM(stock_quantity × purchase_price), gồm cả inactive | 0,00 ₫ |

Giá trị tồn kho chỉ Admin xem; Staff có bốn KPI số lượng. Tổng stock database
chính hiện là 0 nên giá trị 0,00 ₫ và các cảnh báo phản ánh đúng dữ liệu hiện có.
Không thay stock, tạo giao dịch hoặc chạy seed để làm thay đổi kết quả này.
Các con số trên là snapshot báo cáo; HTML/JS runtime không hardcode chúng.

Tính tiền bằng DECIMAL tại MySQL và Decimal tại Python, không float. Giá trị là
ước tính theo giá nhập hiện tại, không gọi là lợi nhuận/giá vốn kế toán.
Nếu giá/stock thiếu hoặc âm, không báo giá trị 0 thay cho dữ liệu sai. Nếu lỗi
truy vấn, trả trang HTTP503 có thông báo và link Thử lại, không trả KPI giả.

Biểu đồ chỉ đếm products active theo category, top 8 và nhóm còn lại nếu có;
bao gồm active product trong category inactive và ghi rõ trạng thái category.
Chart.js 4.5.1/MIT tải từ package chính thức, lưu nội bộ kèm license/SHA-256,
không CDN/CSP mới. Có bảng HTML thay thế, empty state và fallback lỗi thư viện.

Cảnh báo tối đa 8 dòng, ưu tiên tồn kho thấp nhất, đủ SKU/tên/danh mục/stock/
ngưỡng/trạng thái và link chi tiết. Recent tối đa 6 dòng theo thời điểm tạo/cập
nhật gần nhất, gồm inactive theo quyền catalog hiện có; giờ hiển thị Việt Nam.
Không đưa nghiệp vụ nhập/bán hoặc số doanh thu/đơn hàng vào thống kê.

Service có 6 SELECT trong snapshot đọc mới, xác minh isolation chính hiện tại
là REPEATABLE-READ. Backend kiểm tra role, không truy vấn giá nhập hoặc gửi tổng
giá trị tồn kho trong payload Dashboard Staff, kể cả khi sửa query string.
Flask-Login, CSRF, session, rate limiting và audit logging giữ nguyên.

## File tạo mới/chỉnh sửa

| File | Nội dung |
| --- | --- |
| app/services/dashboard_service.py | Mới: aggregate, chart grouping, bounded low stock/recent, quyền trường giá trị |
| app/dashboard/routes.py | Gọi service chỉ đọc; HTTP503 thân thiện; UTC → giờ Việt Nam |
| app/templates/dashboard/business.html | Mới: KPI, chart/bảng fallback, cảnh báo/recent/error/empty, phiên tài khoản |
| app/templates/staff/dashboard.html | Kế thừa template Dashboard mới, giữ layout Staff |
| app/templates/base.html | Block extra_js để chỉ Dashboard tải chart assets |
| app/static/css/dashboard.css | Mới: component responsive, giữ theme/shell hiện tại |
| app/static/js/dashboard.js | Mới: vẽ Chart.js từ dữ liệu server, fallback an toàn |
| app/static/vendor/chartjs/chart.umd.min.js | Mới: Chart.js 4.5.1 lưu local |
| app/static/vendor/chartjs/LICENSE.md | Mới: MIT license |
| app/static/vendor/chartjs/README.md | Mới: provenance, SHA-256, tài liệu tích hợp/accessibility |
| tests/test_dashboard.py | Mới: 22 ca MySQL/route/quyền/error/empty/Decimal/timezone |
| tests/test_auth.py | Cập nhật assertions nội dung Dashboard, giữ các kiểm tra session/quyền |
| scripts/verify_dashboard_ui.py | Mới: KPI/chart/rows đối chiếu MySQL và fallback ở browser |
| docs/DASHBOARD.md | Mới: công thức, quyền, truy vấn, test và bàn giao |
| docs/STAGE_6_REPORT.md | Báo cáo này |
| README.md | Trạng thái và link hướng dẫn Dashboard |
| docs/AUTHENTICATION.md | Phạm vi quyền thống kê Admin/Staff |
| docs/ARCHITECTURE.md | Ranh giới route/service/template và truy vấn chỉ đọc |
| docs/DECISIONS.md | Quyết định 38–40 về phạm vi giữa kỳ |
| .gitignore | Ảnh stage6 sinh tự động giữ local để chọn minh chứng khi commit |

Không thay models, migrations, seed, cấu hình Docker, Python dependencies hoặc
các route/service CRUD. Ảnh stage6 lưu trong docs/screenshots và được ignore;
chưa stage bất kỳ file nào. Ảnh Giai đoạn 4 giữ nguyên.

## Kiểm thử và vận hành

| Kiểm tra | Kết quả cuối |
| --- | --- |
| Backend trong Docker/MySQL thật | **165 passed in 57.99s** = 143 test cũ + 22 Dashboard |
| Dashboard Chromium | 6/6 flows: Admin/Staff × desktop/tablet/mobile |
| Dự phòng biểu đồ | 2/2 chặn thư viện chart; 2/2 không JavaScript, bảng vẫn đọc được |
| Workspace regression | 6/6 flows, login/logout, menu, role, Admin chuyển hai không gian, Staff403 |
| Catalog regression | 6/6 flows, 18 vòng CRUD, 72 POST loading checks |
| Filter/paging/profile regression | 18/18 module/role/viewport flows và no-JS Decimal/validation |
| Database chính | 12/12 bảng có row count/SHA-256 giống baseline trước triển khai |
| Migration | db55d828848e (head); db check không có upgrade operations |
| Local runtime | check-db/nginx config/reload đạt; web/db/nginx healthy; login HTTP200 |
| Mã và secrets | compileall/diff --check đạt; .env ignored, secrets local không có trong file Git-visible |

MySQL test dùng project/volume riêng `techflow-db-tests`, DB `techflow_test`,
host `db-test`; không dùng SQLite thay thế. Test rỗng dùng TEMPORARY TABLE shadow
catalog trên connection riêng, không xóa bảng/dữ liệu test gốc. Có kiểm tra
inactive, 0<=0, dưới/bằng/trên ngưỡng, tổng Decimal lớn/giá 0/phần lẻ, dữ liệu thiếu,
group remainder, limit/thứ tự, Staff không query giá nhập, payload/HTML chống XSS,
error không lộ SQL, route được bảo vệ và timestamp đổi ngày theo múi giờ.

Chromium viewport 1440×1000, 834×1112, 390×844 ở zoom mặc định 100%. KPI, số
trong biểu đồ và ID từng dòng được so với query MySQL độc lập; link chi tiết,
nút Làm mới, role/session, responsive và bảng fallback được thao tác thực tế.
Không có lỗi JavaScript/asset nội bộ ngoài trường hợp chặn thư viện có chủ đích;
không tràn ngang toàn trang. Bảng mobile cuộn trong region riêng, có hướng dẫn.

Đã xem trực tiếp ảnh desktop Admin, tablet Staff, mobile Admin và kiểm tra bố cục.
Thẻ Staff một mình phủ đủ hàng tablet; không tăng font/sidebar toàn giao diện.
Các số trong screenshot là dữ liệu thật của DB test và khác database chính;
fixture test không phải dữ liệu bán hàng hoặc số KPI hardcode.

Lượt đầu sửa fixture TEMPORARY TABLE để tránh alias trùng MySQL, cập nhật test
nhận diện component Dashboard mới, và cho runner nhận URL GET làm mới có dấu
`?` rỗng. Các lỗi này đã được sửa, sau đó full backend/UI đạt. Không nới kiểm
tra quyền, rate limiting hoặc xóa dữ liệu để làm test thành công.

## Screenshot trước/sau

| Vai trò/viewport | Trước | Sau |
| --- | --- | --- |
| Admin desktop | Trước (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) | Sau (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) |
| Admin tablet | Trước (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) | Sau (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) |
| Admin mobile | Trước (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) | Sau (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) |
| Staff desktop | Trước (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) | Sau (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) |
| Staff tablet | Trước (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) | Sau (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) |
| Staff mobile | Trước (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) | Sau (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo) |

Thêm minh chứng: Chart lỗi vẫn đọc bảng (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo),
Staff không JS (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo),
Admin quay về quản trị (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo),
Staff bị chặn quản trị (ảnh cũ đã dọn; xem kết quả kiểm thử trong báo cáo).

## Xem local và bàn giao

Mở http://localhost:8000/login, dùng tài khoản hiện có. Admin mặc định vào
quản trị, chọn **Không gian kinh doanh**; Staff vào Business trực tiếp.
Địa chỉ Dashboard thống kê: http://localhost:8000/staff/dashboard.
Refresh để nhận CSS/JS mới; dùng Làm mới để truy vấn lại. Không cần CLI tạo
tài khoản lại, seed, migration mới hoặc sửa tồn kho.

Snapshot baseline chỉ đọc `.docker-local/stage6-before.json` (ignored) ghi nhận
37 products, 6 categories, 6 businesses, 1 user, 7 audit, 1 stage1_probe,
1 revision; các bảng nhập/bán/movement rỗng. Nội dung toàn bộ bảng giữ nguyên;
không mất account/volume. Test services đã dừng sau nghiệm thu kỹ thuật, volume
giữ nguyên; main services tiếp tục chạy.

Nhóm sau giữa kỳ tiếp tục nghiệp vụ nhập/bán với transaction, cập nhật kho,
báo cáo doanh thu/đơn completed/hoàn hàng, giá vốn và top bán chạy. Đo tải/EXPLAIN
trước khi bổ sung index cho truy vấn timestamp/cảnh báo; LIMIT không loại bỏ
mọi scan/sort. Chưa kiểm thử tải, Safari/Firefox hoặc thiết bị vật lý, chưa AWS.
Không có lỗi chức năng còn ghi nhận trong phạm vi đã kiểm thử.

Lệnh chạy lại và giới hạn chi tiết: [DASHBOARD.md](DASHBOARD.md).
**Dừng chờ người dùng nghiệm thu trước khi commit/push.**
