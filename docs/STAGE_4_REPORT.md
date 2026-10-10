# TechFlow — Báo cáo Giai đoạn 4: Catalog CRUD và hoàn thiện UI/UX

Báo cáo tổng hợp triển khai CRUD, đợt hoàn thiện UI và tinh chỉnh cuối ngày
10/10/2026. Quy ước nhập giá ở phần UI bên dưới là bản cuối, thay hướng dẫn nhập
giá của đợt đầu. Số kiểm thử là kết quả đã nghiệm thu, không chạy lại khi gộp doc.

Đã nghiệm thu, commit `a4529f7` với message
`feat: complete stage 4 catalog CRUD and UI polish` và push theo xác nhận.
Tiếp tục giữ Flask/Jinja2/Bootstrap 5/MySQL/Docker và hai workspace Admin/Business.

## Chức năng và quy tắc

| Module | Chức năng |
| --- | --- |
| Danh mục | CRUD, chi tiết, tìm mã/tên, trạng thái, sort, phân trang |
| Nhà cung cấp | CRUD, tìm mã/tên/email/phone, trạng thái/sort/phân trang, liên kết sản phẩm/phiếu nhập |
| Sản phẩm | CRUD, SKU/tên, lọc danh mục/nhà cung cấp/trạng thái, sort/phân trang, giá VND, brand/model, ngưỡng cảnh báo, URL ảnh/mô tả |

Lưu thật vào MySQL; POST/redirect/GET, validation backend, duplicate/FK error,
404, empty state, loading, flash tiếng Việt và modal xác nhận xóa theo tên.
Không cascade xóa dữ liệu liên kết; sản phẩm còn tồn không được xóa. Có thể
ngừng hoạt động. Sản phẩm mới stock=0; form sửa không nhận stock_quantity từ
client, không tạo movement hoặc nghiệp vụ nhập/bán.

Hai vai trò dùng `business_required` cho catalog; Staff được CRUD theo điều
chỉnh đã duyệt, vẫn bị403 ở quản trị hệ thống. Tồn kho chỉ đọc. Audit create/
update/delete cùng transaction, không sao chép PII/secret. Không float cho tiền.

## Routes, schema và cấu trúc

Prefix: `/business/categories`, `/business/suppliers`, `/business/products`.
Mỗi prefix có GET list/detail/new/edit; POST new/edit và `/{id}/delete` có CSRF.
Blueprint/routes/forms/services/models/templates tách riêng; catalog resources
cấu hình bộ render/routes chung, service whitelist fields/ORM/audit/transaction.

- Categories: code/name UNIQUE; một danh mục có nhiều sản phẩm.
- Businesses: code/tax_code UNIQUE; tax_code trống lưu NULL; schema chưa có loại
  đối tác nên UI quản lý nhà cung cấp.
- Products: SKU UNIQUE, category bắt buộc, supplier tùy chọn, Numeric(14,2),
  stock/reorder unsigned, FK RESTRICT.
- Không migration mới; tại giai đoạn này `db55d828848e (head)`, db check không
  có upgrade operations. Giữ models, dependencies và Docker Compose.

Hướng dẫn đầy đủ: [CATALOG.md](CATALOG.md).

<a id="hoan-thien-ui"></a>
## Hoàn thiện UI và tinh chỉnh cuối

- Giữ navy/xanh dương/nền sáng, typography và hai Dashboard. Không tăng kích
  thước toàn giao diện từ ảnh chụp lúc browser zoom nhỏ.
- Bỏ nhãn MIDTERM/đồ án khỏi giao diện sản phẩm; giữ trạng thái nghiệp vụ chưa
  khả dụng và footer ©2026 TechFlow.
- Form sản phẩm chia cơ bản/phân loại/giá–tồn kho/bổ sung; danh mục có placeholder
  bắt buộc, backend min=1, sửa giữ đúng category_id.
- Form nhà cung cấp chia đối tác/liên hệ/địa chỉ–ghi chú/trạng thái. Chiều rộng
  cuối: danh mục720px, nhà cung cấp900px, sản phẩm1000px; mobile một cột.
  Đồng bộ gap/chiều cao field/footer Lưu–Hủy, không kéo form ngắn quá rộng.
- Filter danh mục/nhà cung cấp desktop một hàng, sản phẩm hai hàng; tablet/
  mobile grid theo chiều rộng, giảm padding/gap, Áp dụng/Xóa lọc thống nhất,
  giữ GET/query/sort/page size và điều kiện lọc khi phân trang.
- Danh sách ưu tiên tên, SKU phụ; giá/tồn căn phải, liên hệ hiện cả phone/email
  khi có, email dài ngắt dòng. Microcopy và flash theo đúng đối tượng.
- Error sát field với aria-invalid/aria-describedby, giữ input khi422/409/503,
  focus lỗi đầu; tooltip/accessible label, modal/keyboard/loading/aria-busy và
  chống submit lặp. Duplicate ánh xạ constraint, không lộ giá trị hoặc SQL.
- “Thông tin cá nhân” trỏ thật `/staff/dashboard#session`, chỉ đọc thông tin
  phiên/tài khoản/role; chưa có profile editor. Không dựng nút chưa hoạt động.

### Nhập giá VND

Nhập `18.500.000,50` hoặc `18500000,50`; dấu chấm nhóm nghìn, dấu phẩy phần
lẻ. Format khi blur, không nhảy con trỏ khi gõ; `18.500` là18.500đ. Chuyển
display→canonical bằng chuỗi, không Number/parseFloat/toFixed/cắt/làm tròn.
Trường có name gốc gửi `18500000.50`, ô hiển thị không gửi tham số trùng.
Backend Decimal/MySQL DECIMAL(14,2) giữ nguyên.

Sai nhóm như `18.500.000.50` báo tại ô/focus đúng, không khóa Lưu. Âm/vượt giới
hạn/quá chính xác vẫn bị backend422. No-JS giữ input number/hướng dẫn chuẩn.
[MDN inputmode](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/inputmode)
và [Number precision](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER#description)
là tài liệu tham khảo của lựa chọn này; backend là nguồn validation cuối.

### Ảnh sản phẩm và bảo mật

Preview browser có loading/success/error và SVG fallback, referrerpolicy
no-referrer. Người dùng đã duyệt riêng HTTP/HTTPS img-src chỉ tại Blueprint
products; script/style/font vẫn self, trang khác giữ CSP. Không server fetch/
proxy/upload/HTML injection hoặc log URL; URL sai/ảnh lỗi về placeholder nội bộ.

Flask-Login, role/session, CSRF, limiter, mật khẩu/CLI Admin và audit giữ nguyên.

## Kiểm thử đã nghiệm thu

| Đợt | Backend MySQL test riêng |
| --- | --- |
| CRUD ban đầu | 135 passed / 38.46s: 85 regression + 39 CRUD + 11 form |
| Hoàn thiện UI | 139 passed / 37.95s: placeholder/category, CSP ảnh, định dạng giá |
| Tinh chỉnh cuối | 143 passed / 29.94s: thêm 4 ca round-trip DECIMAL |

Bao gồm CRUD Admin/Staff; invalid/duplicate/FK, email/phone/URL, tiền âm/NaN/
Infinity/overflow/thừa thập phân, stock giả mạo bị bỏ qua, audit rollback, CSRF,
GET delete405,404, SQL injection/XSS, auth/session/seed/schema/migration cũ.

Browser Chromium tại1440×1000,834×1112,390×844, zoom100%:
6/6 tổ hợp Admin/Staff,18 chu trình CRUD,72 POST/loading; workspace6/6;
filter/paging/profile18/18 cùng no-JS CRUD/precision/validation. Không pageerror/
asset nội bộ lỗi/tràn ngang toàn trang; bảng dài cuộn trong region riêng.
Preview thành công/404/URL sai được kiểm soát qua example.invalid trong browser.

Giá được đọc lại trực tiếp từ MySQL:15000000→0.01,18000000.50→18500000.50;
thử0/0.01/999999999999.99, có/không nhóm nghìn,1,001 không bị làm tròn, số âm.
No-JS lưu giá lớn chính xác, backend chặn giá âm. Filter giữ query, sortA–Z,
status/category/supplier, page size10/20, Tiếp/Trước, empty và Xóa lọc.

Lượt browser chạy chồng từng gặp429 Nginx thật; chạy lại tuần tự đạt, không nới
limiter/auth/CSRF. Compileall, diff --check và scan secrets Git-visible đạt.

## File triển khai

| Nhóm | File tạo/chỉnh sửa chính |
| --- | --- |
| Catalog | app/catalog/{__init__,forms,resources,routes}.py; app/{categories,businesses,products}/routes.py; app/services/catalog_service.py |
| Templates | app/templates/catalog/{base,index,form,detail,delete_modal,fields}.html |
| CSS/JS/ảnh | app/static/css/{catalog,catalog-polish}.css; app/static/js/app.js; app/static/images/product-placeholder.svg |
| Đăng ký/layout/copy/CSP | app/__init__.py; app/templates/{auth/login,layouts/staff,staff/dashboard,admin/dashboard,main/index,errors/error}.html |
| Tests | tests/{test_catalog,test_catalog_forms,test_auth,test_foundation}.py |
| Browser | scripts/{verify_catalog_ui,verify_catalog_polish,verify_ui}.py |
| Tài liệu/ignore | README; CATALOG, ARCHITECTURE, AUTHENTICATION, DECISIONS, SECURITY; .gitignore |

File list bao gồm CRUD và hai đợt UI, không chỉ lần tinh chỉnh cuối.
Ảnh generated dư đã được dọn theo yêu cầu; [danh mục ảnh còn giữ](screenshots/README.md).
Không tạo thêm hoặc xóa ảnh trong lần gộp tài liệu.

## Dữ liệu, truy cập và giới hạn

Mỗi đợt lưu baseline riêng trong `.docker-local`; cả12 bảng khớp count/SHA-256.
Baseline đầu: categories6/businesses6/products36/users1/audit4/probe1; hai đợt
UI sau audit5 do hoạt động hợp lệ đã có trước baseline. Không seed/reset/drop,
sửa tài khoản/mật khẩu/role/stock hoặc xóa volume. Revision giữ nguyên.
Web/db/nginx healthy, check-db và nginx config/reload đạt; login HTTP200.
Services test dừng bằng stop, volumes giữ nguyên.

Truy cập http://localhost:8000/login bằng tài khoản hiện có → Không gian kinh
doanh → Sản phẩm/Danh mục sản phẩm/Nhà cung cấp. CRUD tại demo lưu thật.

Chưa thử Safari/Firefox/thiết bị vật lý hoặc tải lớn; nên xác minh bàn phím dấu
phẩy trên điện thoại thật. Chưa có upload/export/bulk edit/optimistic locking
(lưu sau thắng). Host ảnh có thể chặn hotlink; HTTP ảnh có thể bị chặn dướiHTTPS.
Nhập/bán, khách hàng/bảo hành và KPI thuộc [Giai đoạn5](STAGE_5_REPORT.md)/
[Giai đoạn6](STAGE_6_REPORT.md), không được coi là chức năng Giai đoạn4.
