# CRUD kinh doanh — Giai đoạn 4

Ba module dùng đúng schema `categories`, `businesses`, `products` hiện tại.
`businesses` chỉ mô tả nhà cung cấp; không có cột phân loại đối tác. Không thêm
bảng/cột, framework hay migration. Revision vẫn `db55d828848e`.

## Quyền và routes

| Không gian / chức năng | Admin | Staff |
| --- | --- | --- |
| Admin Dashboard | Có | 403 |
| Business Dashboard | Có | Có |
| CRUD danh mục, nhà cung cấp, sản phẩm | Có | Có |
| Quản lý user, role, cấu hình | Chưa triển khai | Không được cấp quyền |
| Nhập kho, bán hàng, thay đổi tồn kho | Chưa triển khai | Chưa triển khai |

Yêu cầu Giai đoạn 4 mới cho Staff CRUD thay quyền chỉ xem của đặc tả ban đầu;
đã báo cáo khác biệt này trước khi triển khai. Không thay role hoặc session khi
chuyển workspace. Flask-Login, rate limiting, CSRF và audit đăng nhập giữ nguyên.

Với mỗi prefix `/business/categories`, `/business/suppliers`, `/business/products`:

| Phương thức và suffix | Hành vi |
| --- | --- |
| GET (prefix) | Danh sách |
| GET /{id} | Chi tiết |
| GET, POST /new | Thêm mới |
| GET, POST /{id}/edit | Chỉnh sửa |
| POST /{id}/delete | Xóa sau xác nhận |

Blueprint/endpoints: `categories`, `businesses`, `products`, mỗi nhóm có
`index`, `detail`, `create`, `edit`, `delete`. GET delete bị 405.
Tất cả route có `business_required`, mọi POST có CSRF toàn cục.
Thành công ghi dữ liệu trả 303 về detail/list; form sai 422; dữ liệu trùng hoặc
liên kết ngăn thao tác trả 409; không tồn tại 404; lỗi lưu DB khác trả 503.

Query: `q` tối đa 120 ký tự; `status=active|inactive`; `sort=newest|oldest|name|code`;
`page` số dương; `per_page=10|20|50`. Sản phẩm có `category_id`, `business_id`.
Query sai định dạng trả 400. Phân trang giữ các query đang dùng.
Tìm mã/tên, nhà cung cấp tìm thêm email/điện thoại. ORM bind tham số và escape
wildcard `%`, `_`; không nối input thành SQL. Sort dùng allowlist.

## Validation và dữ liệu

- Mã/SKU bắt buộc, chuẩn hóa chữ hoa, cho phép chữ không dấu/số và `. _ / -`.
  Giới hạn độ dài đúng model. Tên bắt buộc, trim khoảng trắng; tên danh mục unique.
- Nhà cung cấp dùng các cột thực: mã, tên, mã số thuế, người liên hệ, email,
  điện thoại, địa chỉ, ghi chú, trạng thái. Email kiểm tra định dạng, không DNS;
  điện thoại 7–15 chữ số, cho phép dấu +/khoảng trắng/dấu phân cách thông dụng.
  Mã số thuế trống lưu NULL, các giá trị có nội dung vẫn chịu unique constraint.
- Sản phẩm có SKU, tên, danh mục bắt buộc, nhà cung cấp tùy chọn, brand/model,
  giá nhập/bán, ngưỡng cảnh báo, URL hình ảnh, mô tả, trạng thái. FK phải nằm
  trong các lựa chọn từ DB; DB vẫn kiểm tra FK nếu bản ghi bị xóa đồng thời.
- Giá dùng Decimal, không float, hữu hạn từ 0 đến 999999999999.99 và tối đa
  hai chữ số thập phân. Nhập ví dụ `15000000.50`; giao diện hiển thị `15.000.000,50 ₫`.
- Ngưỡng cảnh báo số nguyên 0–4294967295; mô tả/ghi chú tối đa 4000 ký tự.
  URL ảnh tối đa 500 ký tự, HTTP/HTTPS, không credentials/control characters;
  có preview trên trình duyệt và liên kết mở tab mới, không server fetch/upload ảnh.
- Tồn kho không có trong form/whitelist lưu. Sản phẩm mới stock=0; sửa không
  ghi lại tồn kho, kể cả client tự thêm `stock_quantity` vào POST. Không phát
  sinh stock movement, phiếu nhập, đơn bán hoặc doanh thu.
- Có thể chọn quan hệ đang ngừng hoạt động (được ghi rõ trong lựa chọn);
  trạng thái dùng để quản lý danh mục, chưa phải quy tắc cho nghiệp vụ nhập/bán.

## Xóa và audit

FK ON DELETE RESTRICT hiện có bảo vệ danh mục có sản phẩm, nhà cung cấp có sản
phẩm/phiếu nhập và sản phẩm có chi tiết nhập/bán hoặc stock movement. Không
cascade. Sản phẩm còn tồn kho cũng bị chặn; SELECT FOR UPDATE giữ khóa sản phẩm
đến khi commit. Dùng ngừng hoạt động khi không thể xóa.

Service commit bản ghi và AuditLog cùng transaction, rollback cả hai khi lỗi.
Audit action `create|update|delete`, entity_type tên bảng, entity_id ID bản ghi,
user_id tài khoản hiện tại. Nội dung audit cố định, không sao chép thông tin
liên hệ, mật khẩu hoặc token. IP tiếp tục là IP proxy hiện tại như thiết kế auth.

Chi tiết danh mục/nhà cung cấp có số sản phẩm liên kết và link tới bộ lọc thật.
Nhà cung cấp có số phiếu nhập và 10 phiếu gần nhất nếu đã có dữ liệu; chỉ đọc,
không tạo hoặc xử lý phiếu nhập. Timestamp hiển thị UTC có nhãn rõ ràng.

## Bàn giao và kiểm tra trực tiếp

Đăng nhập tại http://localhost:8000/login bằng tài khoản đã tạo. Admin chọn
**Không gian kinh doanh**. Dùng sidebar mở ba module; tạo một danh mục và nhà
cung cấp, sau đó thêm sản phẩm với hai liên kết đó. Kiểm tra sửa/tìm/lọc và thử
xóa danh mục khi sản phẩm còn liên kết để thấy thông báo bảo vệ. Xóa sản phẩm
test trước rồi xóa danh mục/nhà cung cấp test nếu không cần giữ.

Các thao tác này lưu thật vào database demo. Không chạy seed lại, reset database
hay xóa volume. Dùng runner test riêng để kiểm thử tự động; scripts browser có
guard `APP_ENV=testing`, DB `techflow_test`/host `db-test` trước khi tạo account.

Hạn chế MVP: chưa có optimistic locking cho hai người sửa cùng bản ghi (lần lưu
sau thắng), chưa có upload ảnh, export, bulk edit hay màn hình audit. Giai đoạn 5
sẽ bổ sung nhập/bán, transaction cập nhật tồn kho, khóa hàng và chống xử lý lặp;
không đặt các chức năng đó vào CRUD catalog.

## Hoàn thiện UI/UX trước nghiệm thu

Form sản phẩm chia bốn nhóm: cơ bản, phân loại, giá/tồn kho, thông tin bổ sung.
Tạo mới bắt đầu với “Chọn danh mục”; giá trị 0 bị backend từ chối, form sửa giữ
nguyên ID đã lưu. Nhà cung cấp chia thông tin đối tác/liên hệ/địa chỉ–ghi chú/
trạng thái; địa chỉ rộng toàn hàng. Danh mục dùng bố cục gọn. Cả ba dùng chung
macro field, metadata groups, validation gần input và Lưu/Hủy cuối form.

Khi JavaScript hoạt động, ô giá dùng định dạng Việt Nam: `15.000.000,50` hoặc
`15000000,50`. Dấu chấm là phân cách hàng nghìn, dấu phẩy là phần thập phân:
`18.500` nghĩa là 18.500 đồng, còn `18,50` nghĩa là 18,50 đồng. Chỉ format khi
rời ô để không làm nhảy con trỏ. Chuỗi sai nhóm như `18.500.000.50` bị chặn tại
ô nhập, có thông báo và focus; nút Lưu vẫn dùng được sau khi sửa.

JS tạo ô hiển thị không có name; trường hidden có name gốc gửi chuỗi chuẩn
`15000000.50`. Chuyển đổi chỉ bằng chuỗi, không Number/parseFloat/toFixed,
không cắt hoặc làm tròn phần lẻ. Giá âm, vượt giới hạn, quá độ chính xác được
gửi nguyên giá trị chuẩn để backend Decimal kiểm tra như trước; response 422
giữ dữ liệu và focus tới trường lỗi. MySQL vẫn DECIMAL(14,2), không migration.
Nếu tắt JS, form gốc dùng input number và hướng dẫn chuẩn `15000000.50`;
backend vẫn không nhận dấu phân cách Việt Nam trực tiếp.

Loading vô hiệu hóa nút và chặn submit lặp trong cùng form đang xử lý. Form bị
chặn vì sai định dạng ở client không bật loading. Preview không sửa giá.

Tên sản phẩm là cột chính, SKU phụ bên dưới; giá/tồn kho căn phải. Nhà cung cấp
hiển thị cả phone/email nếu có. Filter dùng grid responsive, có trạng thái đang
áp dụng, giữ query khi phân trang. Icon action có accessible label và tooltip.
Bảng mobile cuộn riêng, có hướng dẫn vuốt và hỗ trợ focus bàn phím.

Bộ lọc danh mục/nhà cung cấp trên desktop gom thành một hàng; sản phẩm hai
hàng có nút thao tác cùng hàng sắp xếp/số dòng. Tablet/mobile chuyển grid theo
chiều rộng, không tràn toàn trang. Form danh mục tối đa 720px, nhà cung cấp
900px, sản phẩm 1000px; trường và footer dùng cùng hệ thống spacing.

“Thông tin cá nhân” trỏ tới `/staff/dashboard#session`, là phần thông tin phiên
và vai trò hiện tại chỉ đọc. Link hoạt động từ cả ba module cho Admin và Staff;
chưa có chức năng chỉnh sửa hồ sơ. Sidebar quản trị vẫn dùng `#account` thật.

Theo xác nhận riêng của người dùng, CSP chỉ mở img-src HTTP/HTTPS ngoài trên
Blueprint products; script/style/font vẫn self, các trang khác giữ CSP cũ.
Preview tải trực tiếp trên browser, không referrer, không log URL, không chèn
HTML. URL không hợp lệ hoặc ảnh lỗi về SVG nội bộ; không ngăn lưu URL hợp lệ
chỉ vì host ảnh tạm lỗi. HTTP ảnh có thể bị browser chặn trên trang HTTPS;
nên dùng HTTPS cho ảnh. Upload và proxy tải ảnh chưa triển khai.

Giao diện không còn nhãn đồ án/giai đoạn/giữa kỳ; footer © 2026 TechFlow.
Mã/tên/email seed trong DB giữ nguyên. Chi tiết nghiệm thu và ảnh trước/sau:
[STAGE_4_UI_REPORT.md](STAGE_4_UI_REPORT.md).
