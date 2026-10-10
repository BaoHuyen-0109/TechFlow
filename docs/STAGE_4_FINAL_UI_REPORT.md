# TechFlow — Tinh chỉnh UI/UX cuối Giai đoạn 4

Ngày: 10/10/2026, giờ Việt Nam. Đã cập nhật website Docker local.
**Người dùng đã nghiệm thu và cho phép tạo commit local. Không tự động push.**

## Kết quả thay đổi

- Giữ hệ thống navy/xanh dương/nền sáng, typography và sidebar hiện có. Không
  tăng kích thước toàn giao diện theo ảnh zoom nhỏ. Không sửa hai Dashboard,
  route hoặc quyền truy cập.
- Filter danh mục/nhà cung cấp desktop cùng một hàng: tìm kiếm, trạng thái,
  sắp xếp, số dòng và nút Áp dụng/Xóa lọc. Filter sản phẩm dùng hai hàng, nút
  cùng hàng sắp xếp/số dòng; tablet/mobile chuyển grid theo chiều rộng. Giảm
  padding/gap riêng bộ lọc, giữ toàn bộ tham số GET và trạng thái phân trang.
- Form danh mục tối đa 720px, nhà cung cấp 900px, sản phẩm 1000px. Đồng bộ gap
  giữa field, khoảng cách nhóm và chiều cao input; footer Lưu/Hủy dùng chung.
  Không ép form ngắn phủ hết vùng nội dung.
- Giá VND nhập `18.500.000,50` hoặc `18500000,50`, format khi blur, không làm
  nhảy con trỏ trong lúc gõ. Dấu chấm nhóm nghìn; dấu phẩy là phần lẻ. Hướng dẫn
  đặt ngay dưới ô giá. `18.500` nghĩa là 18.500 đồng, không phải 18,5 đồng.
- Chuyển display → canonical bằng thao tác chuỗi, không Number/parseFloat/
  toFixed, không cắt/làm tròn phần thập phân. Trường có name gốc gửi giá chuẩn
  như `18500000.50`; ô hiển thị không có name nên không gửi trùng tham số.
  Backend Decimal và MySQL DECIMAL(14,2) giữ nguyên.
- Sai nhóm nghìn như `18.500.000.50` báo ngay tại input, focus đúng chỗ, không
  khóa nút Lưu. Giá âm/vượt giới hạn/quá độ chính xác vẫn được backend từ chối
  với 422, giữ dữ liệu form. Khi không JS, form number/hướng dẫn chuẩn ban đầu
  vẫn hoạt động, không có hidden field thay thế.
- Rà soát sidebar: “Thông tin cá nhân” là link thật tới
  `/staff/dashboard#session`, hiển thị thông tin phiên/tài khoản/vai trò chỉ đọc;
  chưa có chỉnh sửa hồ sơ. Đã kiểm tra link từ cả ba module cho hai vai trò.
  Admin dùng Không gian kinh doanh/Quay về quản trị như trước; Staff bị 403.
  Các nghiệp vụ chưa có vẫn không có liên kết thao tác.

Lựa chọn text input có `inputmode=decimal` hỗ trợ bàn phím nhập số; browser/
thiết bị quyết định kiểu phím thực tế ([MDN inputmode](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/inputmode)).
Tránh chuyển giá qua số thực vì độ chính xác Number phụ thuộc độ lớn của giá trị
([MDN Number precision](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER#description)).
Validation backend vẫn là nguồn kiểm tra cuối cùng, không phụ thuộc JS.

## File trong đợt tinh chỉnh này

| File | Thay đổi |
| --- | --- |
| app/static/css/catalog-polish.css | Grid filter, chiều rộng form theo module, spacing/chiều cao field |
| app/static/js/app.js | Adapter giá Việt Nam; chặn loading khi submit đã bị ngăn |
| app/templates/catalog/fields.html | Đánh dấu field giá để progressive enhancement |
| app/templates/catalog/form.html | Class form riêng theo resource |
| tests/test_catalog.py | Thêm 4 ca round-trip DECIMAL trên MySQL |
| scripts/verify_catalog_ui.py | Kiểm tra adapter, invalid format, giá trị chuẩn, đọc lại giá lưu thật |
| scripts/verify_catalog_polish.py | Mới: filter/paging/profile cả hai role, no-JS lưu/validation |
| docs/CATALOG.md | Quy ước giá, fallback, filter/form và link thông tin cá nhân |
| docs/DECISIONS.md | Quyết định mới thay hướng dẫn giá của đợt trước |
| docs/STAGE_4_UI_REPORT.md | Liên kết tới báo cáo mới; giữ lịch sử đợt trước |
| README.md | Liên kết tài liệu nghiệm thu mới |
| docs/STAGE_4_FINAL_UI_REPORT.md | Báo cáo này |
| docs/screenshots/stage4-final-*.png | 108 ảnh mới ở local; chỉ version các ảnh được tài liệu tham chiếu |

Bảng trên chỉ liệt kê file trong đợt tinh chỉnh cuối. Commit nghiệm thu gồm
cả CRUD và các đợt UI Giai đoạn 4. Không migration/dependency/config Docker mới.
Chỉ giữ 44 screenshot được tài liệu tham chiếu trong Git; 232 ảnh còn lại giữ
ở local, được ignore, không xóa. Các số lượng ảnh kiểm thử bên dưới mô tả đầy
đủ lượt chạy tại local, không yêu cầu đưa toàn bộ ảnh vào repository.

## Kiểm thử

| Bộ kiểm tra | Kết quả |
| --- | --- |
| pytest trong Docker, MySQL 8 riêng | **143 passed in 29.94s**, gồm toàn bộ 139 ca trước và 4 ca Decimal mới |
| Browser CRUD | **6/6 role/viewport flows**, 18 vòng thêm/sửa/xóa, 72 POST có loading |
| Filter/paging/profile | **18/18 module/role/viewport flows**, cùng kiểm tra fallback không JS |
| Workspace regression | **6/6 flows**, login, role, menu/collapse, điều hướng, Admin chuyển không gian, Staff403, logout |
| JavaScript/asset/overflow | Không pageerror/asset nội bộ lỗi; không tràn ngang toàn trang ở các kiểm tra viewport |
| Integrity database chính | **12/12 bảng** cùng số dòng và SHA-256 trước/sau |
| Migration | **db55d828848e (head)**; db check không có upgrade operations |
| Vận hành | check-db đạt; nginx config/reload đạt; web/db/nginx healthy; `/login` HTTP200 |
| Kiểm tra mã | compileall và diff --check đạt; local secrets không có trong file Git-visible; index rỗng |

Viewport Chromium: desktop **1440×1000**, tablet **834×1112**, mobile **390×844**,
zoom mặc định 100%, không CSS zoom. Đã xem trực tiếp ảnh filter desktop,
form danh mục desktop, form sản phẩm desktop/mobile và danh sách tablet.
Bảng dài cuộn trong region riêng; form mobile xếp một cột.

Browser kiểm tra thêm: tìm mã/tên, trạng thái active/inactive, sort A–Z,
category/supplier kết hợp, page size 10/20, Tiếp/Trước giữ nguyên query,
đổi page size về trang đầu, empty state và Xóa lọc. Fixture 11 dòng mỗi module
được tạo/chỉ dọn trong `techflow_test` qua guard host `db-test`/APP_ENV testing.

Adapter kiểm tra 0, 0,01, 999.999.999.999,99, giá có/không nhóm nghìn,
1,001 không bị làm tròn, 18.500 và số âm. CRUD browser đọc lại trực tiếp
DECIMAL sau create/edit: 15000000 → 0.01 và 18000000.50 → 18500000.50.
Không JS cũng tạo sản phẩm với 999999999999.99/0.01, đọc lại MySQL chính xác,
và backend từ chối sửa thành số âm. Các test backend từ chối input locale
gửi trực tiếp vẫn giữ nguyên và đạt.

Hai lượt browser đầu bị 429 vì chạy các runner đồng thời qua cùng IP Nginx;
log xác nhận `limiting requests` tại POST /login. Chạy lại tuần tự đạt toàn bộ.
Không nới hoặc tắt rate limiting/authentication/CSRF để kiểm thử.

## Ảnh trước/sau

Ảnh trước là đợt UI ngay trước lần tinh chỉnh này, cùng viewport/zoom; dữ liệu
trong ảnh là fixture riêng mỗi lượt chạy. Ảnh full-page có thể cao hơn viewport.

| Nội dung | Trước | Sau |
| --- | --- | --- |
| Filter danh mục desktop | [Trước](screenshots/stage4-ui-admin-categories-desktop.png) | [Sau](screenshots/stage4-final-admin-categories-desktop.png) |
| Filter sản phẩm tablet | [Trước](screenshots/stage4-ui-staff-products-tablet.png) | [Sau](screenshots/stage4-final-staff-products-tablet.png) |
| Form danh mục gọn | [Trước](screenshots/stage4-ui-admin-categories-form-desktop.png) | [Sau](screenshots/stage4-final-admin-categories-form-desktop.png) |
| Form giá VND desktop | [Trước](screenshots/stage4-ui-admin-products-form-desktop.png) | [Sau](screenshots/stage4-final-admin-products-form-desktop.png) |
| Form sản phẩm mobile | [Trước](screenshots/stage4-ui-staff-products-form-mobile.png) | [Sau](screenshots/stage4-final-staff-products-form-mobile.png) |

Minh chứng thêm: [validation mobile](screenshots/stage4-final-staff-validation-mobile.png),
[nhà cung cấp tablet](screenshots/stage4-final-admin-suppliers-form-tablet.png),
[Admin quay về quản trị](screenshots/stage4-final-regression-admin-return-desktop.png),
[Staff bị chặn](screenshots/stage4-final-regression-staff-403-mobile.png).

## Lặp lại kiểm thử và bàn giao

Chạy tuần tự, từ E:\AWS, Docker Engine hoạt động và `.env` local đã thiết lập:

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
docker compose -f docker-compose.db-test.yml --profile ui up -d --wait --wait-timeout 120 ui-nginx
docker compose -f docker-compose.db-test.yml exec -T ui-nginx nginx -s reload
.\.venv\Scripts\python.exe scripts/verify_catalog_ui.py --screenshot-prefix stage4-final
.\.venv\Scripts\python.exe scripts/verify_catalog_polish.py
.\.venv\Scripts\python.exe scripts/verify_ui.py --screenshot-prefix stage4-final-regression
docker compose -f docker-compose.db-test.yml --profile ui stop ui-nginx ui db-test
```

Browser runner cần môi trường `requirements-ui.txt` và Chromium đã chuẩn bị.
Đổi prefix nếu cần giữ thêm ảnh của lượt nghiệm thu khác. Không chạy các runner
song song để tránh giới hạn đăng nhập theo IP. Test services đã dừng sau nghiệm
thu, toàn bộ volume giữ nguyên. Main services vẫn chạy.

Database chính snapshot chỉ đọc tại `.docker-local/stage4-final-before.json`
(ignored): 6 categories, 6 businesses, 36 products, 1 user, 5 audit, 1 probe,
1 alembic revision, các bảng nhập/bán/movement rỗng. Không seed/reset/drop,
không sửa account/mật khẩu/role, không xóa volume hoặc dữ liệu chính.

Mở http://localhost:8000/login, dùng tài khoản hiện có; Admin vào Không gian
kinh doanh rồi chọn ba module. Refresh trang để tải CSS/JS mới. CRUD ở website
chính vẫn lưu thật vào database; dữ liệu kiểm thử tự động chỉ ở database riêng.

Không có lỗi chức năng còn ghi nhận sau lượt kiểm tra cuối. Giới hạn: chỉ
Chromium/viewport mô phỏng, chưa Safari/Firefox/thiết bị vật lý; nên kiểm tra
thêm bàn phím dấu phẩy trên điện thoại thực. Không có profile editor, KPI mới,
biểu đồ, doanh thu/đơn hàng giả, nhập kho/bán hàng, Giai đoạn 5/6 hoặc AWS.

**Đã nghiệm thu; lưu bằng commit local theo yêu cầu. Chưa push và chưa chuyển giai đoạn.**
