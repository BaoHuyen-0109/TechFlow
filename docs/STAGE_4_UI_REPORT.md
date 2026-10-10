# Hoàn thiện UI/UX Giai đoạn 4 — TechFlow

Đây là báo cáo đợt UI đầu tiên. Tinh chỉnh mới nhất, quy ước nhập giá Việt Nam
và kết quả nghiệm thu bổ sung tại [STAGE_4_FINAL_UI_REPORT.md](STAGE_4_FINAL_UI_REPORT.md).

Ngày nghiệm thu kỹ thuật: 10/10/2026, giờ Việt Nam. Đã cập nhật Docker local;
**chưa commit/push**, dừng chờ người dùng xem giao diện.

## Vấn đề và thay đổi

| Vấn đề trước chỉnh sửa | Kết quả |
| --- | --- |
| Nhãn giữa kỳ/MIDTERM và nội dung tiến độ ở Login, footer, trang chủ, Dashboard | Bỏ nhãn đồ án; footer © 2026 TechFlow, mô tả theo chức năng. Giữ thông báo tính năng chưa khả dụng |
| Form sản phẩm là danh sách field liên tiếp | Bốn nhóm cơ bản/phân loại/giá–tồn kho/bổ sung, dùng chung cho thêm/sửa và chi tiết |
| Danh mục đầu danh sách dễ được chọn ngoài ý muốn | Placeholder “Chọn danh mục”, backend từ chối 0; sửa giữ đúng category_id đã lưu |
| Giá chưa giải thích rõ dấu phân cách | Hướng dẫn không phân tách hàng nghìn, dấu chấm thập phân, ví dụ 15000000.50. Không format hoặc làm tròn input |
| Chỉ có link ảnh, chưa có preview | Preview trên browser, trạng thái đang tải/thành công/lỗi, fallback SVG nội bộ, referrerpolicy no-referrer |
| Form nhà cung cấp chưa phân nhóm | Tách đối tác/liên hệ/địa chỉ–ghi chú/trạng thái; địa chỉ toàn hàng |
| Mô tả các trang lặp lại | Microcopy riêng cho từng module/thêm/sửa; nút Lưu theo đối tượng |
| SKU đứng trước tên sản phẩm | Tên là thông tin chính, SKU phụ bên dưới; giá/tồn kho căn phải, số hiển thị VND thống nhất |
| Liên hệ chỉ hiển thị phone hoặc email | Hiển thị cả hai nếu có, email dài được ngắt dòng, không có thì báo “Chưa có liên hệ” |
| Filter nhiều trường trên một hàng | Grid desktop/tablet/mobile; cụm Áp dụng/Xóa lọc rõ, báo đang áp dụng filter, giữ query khi phân trang |
| Lỗi duplicate/FK còn chung chung | Thông báo theo mã SKU/mã hoặc tên danh mục/mã hoặc thuế nhà cung cấp; FK báo đúng đối tượng |

Giữ nguyên theme navy/sáng/xanh dương, Bootstrap 5/Jinja2, hai Dashboard/layout
riêng và điều hướng chuyển workspace. Sidebar 244/80px, offcanvas, nhóm menu,
title/accessible label khi thu gọn được giữ và kiểm tra lại. Icon CRUD có tooltip
Bootstrap thật, accessible label; modal vẫn xác nhận bằng tên bản ghi.

## Form và thao tác

- Sản phẩm: SKU/tên/brand/model; category/supplier; giá nhập/bán/ngưỡng cảnh báo;
  URL ảnh/mô tả/trạng thái. Tồn kho nằm trong vùng chỉ xem, không có input ghi stock.
- Danh mục: bố cục gọn mã/tên, mô tả toàn hàng, trạng thái, Lưu/Hủy nhất quán.
- Nhà cung cấp: các field thực theo schema, email/phone/tax giữ validation cũ;
  địa chỉ/ghi chú đủ rộng. Không thêm dữ liệu hoặc trường giả.
- Error sát field, aria-invalid/aria-describedby, giữ input khi 422/409/503;
  focus trường sai đầu tiên. Lưu có spinner/aria-busy, vô hiệu hóa nút và chặn
  submit lặp khi form đang xử lý. Hủy trở về đúng detail/list.
- Flash: “Thêm sản phẩm thành công”, “Cập nhật danh mục thành công”, “Xóa nhà cung
  cấp thành công”…; không thay transaction/audit hoặc nghiệp vụ xóa.

## Phạm vi backend và bảo mật

Thay backend nhỏ có chủ đích: metadata nhóm/nhãn; placeholder category và kiểm
tra min=1 để giữ yêu cầu danh mục bắt buộc; flash theo đối tượng; ánh xạ tên
unique constraint thành thông báo thân thiện. Không hiển thị hoặc log duplicate
value/SQL. FK và quy tắc tồn kho vẫn như cũ; audit cùng transaction.

Người dùng đã xác nhận riêng cho phép ảnh HTTP/HTTPS bên ngoài trên trang sản
phẩm sau khi tự động duyệt yêu cầu xác nhận việc mở nguồn ảnh. CSP chỉ mở img-src
tại Blueprint products; script/style/font vẫn self, các trang khác giữ CSP cũ.
Browser tải ảnh trực tiếp, không server fetch/proxy, không HTML injection, không
console log URL, không referrer. URL sai hoặc ảnh lỗi về SVG nội bộ. Không upload.

Flask-Login, role/session, CSRF, rate limiting, mật khẩu, CLI Admin, audit,
models, requirements, migrations, Docker Compose và schema giữ nguyên.

## File trong đợt hoàn thiện này

| Nhóm | File |
| --- | --- |
| Form/group/microcopy | app/catalog/resources.py, app/catalog/forms.py, app/catalog/routes.py |
| Lỗi CRUD | app/services/catalog_service.py |
| Render catalog | app/templates/catalog/base.html, form.html, detail.html, index.html; mới fields.html |
| UI/preview/loading/tooltip | app/static/js/app.js; mới app/static/css/catalog-polish.css |
| CSP ảnh theo workspace | app/__init__.py |
| Nội dung giao diện | app/templates/auth/login.html, layouts/workspace.html, main/index.html, admin/dashboard.html, staff/dashboard.html |
| Tests | tests/test_catalog.py, test_catalog_forms.py, test_auth.py, test_foundation.py, scripts/verify_catalog_ui.py |
| Bàn giao | README.md, docs/CATALOG.md, ARCHITECTURE.md, SECURITY.md, DECISIONS.md, STAGE_4_REPORT.md; mới STAGE_4_UI_REPORT.md |
| Minh chứng | 84 ảnh stage4-ui-* và 24 ảnh stage4-ui-regression-* trong docs/screenshots |

Các file CRUD Giai đoạn 4 có sẵn vẫn được giữ. `git diff` so với commit Giai đoạn
3 bao gồm cả CRUD trước đó và đợt này; không reset, bỏ thay đổi hay stage/commit.

## Kết quả kiểm thử

```powershell
docker compose -f docker-compose.db-test.yml run --build --rm tests
```

**139 passed in 37.95s**, không fail/skip trong lần chạy cuối trên MySQL 8 thật,
DB techflow_test/host db-test, volume và project riêng. Gồm regression Giai đoạn
1–4, CRUD Admin/Staff, CSRF, inactive/role, validation, duplicate/FK, missing404,
search/filter/sort/pagination, audit rollback và bảo vệ stock/không tạo nghiệp vụ.

So với 135 tests ban đầu, thêm kiểm tra placeholder/sửa giữ danh mục, CSP ảnh
chỉ mở ở products và hai trường hợp định dạng giá không hợp lệ. Bổ sung assertions
thông báo duplicate cụ thể/giữ input khi backend lỗi. Hai assertion microcopy
cũ của trang chủ/Business được cập nhật vì nội dung đồ án đã gỡ; không bỏ kiểm
tra quyền hay xác thực. Một lần chạy đầu phát hiện assertion copy cũ; đã sửa,
không có lỗi chức năng còn tồn tại trong phạm vi test.

Compile Python và git diff --check đạt; Git chỉ cảnh báo quy đổi LF/CRLF.

## Playwright và xem ảnh thực tế

```powershell
docker compose -f docker-compose.db-test.yml --profile ui up -d --wait ui-nginx
docker compose -f docker-compose.db-test.yml exec -T ui-nginx nginx -s reload
.\.venv\Scripts\python.exe scripts/verify_catalog_ui.py --screenshot-prefix stage4-ui
.\.venv\Scripts\python.exe scripts/verify_ui.py --screenshot-prefix stage4-ui-regression
```

Chromium, Admin/Staff × **1440×1000 / 834×1112 / 390×844**:

- CRUD: **6/6 luồng đạt**, **18 vòng CRUD thật**, **72 POST loading checks**.
  Gồm form thêm/sửa/detail/list, danh mục mặc định/sửa giữ nguyên, focus lỗi,
  giữ input, preview URL sai/ảnh404/ảnh thành công, lọc liên kết, giá VND,
  modal hủy/xác nhận, chặn xóa liên kết, empty state sau xóa.
- Workspace regression: **6/6 luồng đạt**; login username/email, session/redirect,
  logout, Admin chuyển qua lại giữ role/phiên, Staff403, 404, collapse/offcanvas,
  hover/focus, active menu và các link thực.
- Không có JavaScript pageerror, asset nội bộ lỗi hoặc tràn ngang toàn trang.
  Bảng mobile cuộn trong region riêng; modal nằm trong viewport.
- Preview dùng host example.invalid được Playwright trả ảnh/lỗi có kiểm soát,
  kiểm tra CSP và load/error thật của browser; không phụ thuộc Internet/host ảnh
  bên thứ ba. CRUD vẫn được thực hiện thật trên MySQL test.
- Đã xem trực tiếp ảnh form desktop, danh mục desktop, nhà cung cấp tablet,
  danh sách/form sản phẩm mobile và modal mobile. Form chia nhóm rõ, không cắt
  field; ảnh preview/placeholder nằm gọn, email không vỡ bảng, action nhất quán.
- Chụp full-page từ đầu trang để tránh Chromium ghi fixed sidebar ở vị trí cuộn
  của input; ảnh full-page cao hơn viewport là bình thường. Ảnh trước giữ nguyên.

## Screenshot trước/sau

| Nội dung | Trước | Sau |
| --- | --- | --- |
| Form sản phẩm desktop | [Trước](screenshots/stage4-admin-product-form-desktop.png) | [Sau](screenshots/stage4-ui-admin-products-form-desktop.png) |
| Sản phẩm mobile | [Trước](screenshots/stage4-staff-products-mobile.png) | [Sau](screenshots/stage4-ui-staff-products-mobile.png) |
| Business Dashboard | [Trước](screenshots/stage4-regression-admin-business-desktop.png) | [Sau](screenshots/stage4-ui-admin-business-desktop.png) |
| Danh mục | [Trước](screenshots/stage4-admin-categories-desktop.png) | [Sau](screenshots/stage4-ui-admin-categories-desktop.png) |
| Nhà cung cấp | [Trước](screenshots/stage4-admin-suppliers-desktop.png) | [Sau](screenshots/stage4-ui-admin-suppliers-desktop.png) |

Minh chứng thêm:

- [Sửa sản phẩm](screenshots/stage4-ui-admin-products-edit-desktop.png),
  [chi tiết](screenshots/stage4-ui-admin-products-detail-desktop.png),
  [form mobile](screenshots/stage4-ui-staff-products-form-mobile.png).
- [Form danh mục](screenshots/stage4-ui-admin-categories-form-desktop.png),
  [form nhà cung cấp tablet](screenshots/stage4-ui-admin-suppliers-form-tablet.png).
- [Modal mobile](screenshots/stage4-ui-staff-delete-modal-mobile.png),
  [validation](screenshots/stage4-ui-staff-validation-mobile.png),
  [ảnh lỗi/fallback](screenshots/stage4-ui-staff-image-fallback-mobile.png).
- [Login](screenshots/stage4-ui-regression-login-desktop.png),
  [Admin quay về quản trị](screenshots/stage4-ui-regression-admin-return-desktop.png),
  [Staff403](screenshots/stage4-ui-regression-staff-403-mobile.png).

## Database và vận hành

Snapshot chỉ đọc trước đợt chỉnh sửa tại `.docker-local/stage4-ui-before.json`
(ignored). Sau rebuild, đối chiếu **12/12 bảng có số dòng và SHA-256 giống hệt**:
6 categories, 6 businesses, 36 products, 1 user, 5 audit, stage1_probe 1 dòng,
các bảng nhập/bán/movement 0. Khác số audit so với báo cáo CRUD trước là trạng
thái có sẵn trước đợt này; toàn bộ nội dung giữ nguyên theo baseline mới.

Không chạy seed, reset DB/xóa volume, sửa tài khoản/mật khẩu/role hoặc cập nhật
stock. Revision vẫn **db55d828848e (head)**; db check không có upgrade operations.
check-db đạt; nginx config/reload đạt; web/db/nginx healthy. Test services dừng
sau kiểm thử, volume giữ nguyên. Không AWS hoặc chức năng Giai đoạn 5.

## Truy cập và giới hạn

Mở http://localhost:8000/login bằng tài khoản hiện có; Admin chọn Không gian kinh
doanh, rồi mở sản phẩm/danh mục/nhà cung cấp. Có thể refresh để lấy CSS/JS mới.
Các thao tác CRUD trực tiếp vẫn lưu thật vào database đang dùng.

Chỉ kiểm Chromium với viewport mô phỏng, chưa Safari/Firefox/thiết bị vật lý.
Host ảnh bên ngoài có thể chặn hotlink hoặc tạm lỗi; fallback không ngăn lưu URL
hợp lệ. HTTP ảnh có thể bị chặn khi app chạy HTTPS. Chưa có upload/thumbnail trong
bảng, kiểm thử tải, optimistic locking, nhập/bán hàng hay báo cáo doanh thu.

**Dừng chờ người dùng duyệt giao diện. Giai đoạn 4 vẫn chưa commit/push.**
