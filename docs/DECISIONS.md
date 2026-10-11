# Quyết định kỹ thuật

1. Dùng PyMySQL để tránh dependency biên dịch driver; Python 3.12 trong Docker.
2. URL.create xây URL database từ các biến thành phần, tránh lỗi ký tự đặc biệt
   trong password. DATABASE_URL là override tùy chọn; phải tự URL-encode credentials.
3. Không fallback secret hoặc database. Ứng dụng từ chối khởi động khi cấu hình thiếu.
4. Giai đoạn 1 dùng ba service để kiểm tra cùng đường đi Nginx → Gunicorn → MySQL.
   MySQL dùng utf8mb4/InnoDB mặc định, named volume, không publish cổng.
5. Giai đoạn 1 chưa có schema. Flask-Migrate được bind nhưng `db upgrade` chỉ có
   ý nghĩa sau khi bổ sung migrations ở giai đoạn 2.
6. Test nền tảng dùng Flask test client và mock kết nối để chạy độc lập, không
   tạo/xóa bảng. Đây không phải test tích hợp MySQL. `check-db` chạy thật là bước riêng.
7. Dành package cho module tương lai; không viết service nghiệp vụ giả hoặc route giả.
8. Chưa tạo cấu hình triển khai AWS/HTTPS production trong giai đoạn 1. Config Python
   có validation production nhưng Compose hiện tại chỉ dành cho local HTTP.
9. Dừng ở giai đoạn 1 chờ người dùng xác nhận; không tự chuyển sang models/migrations.

## Giai đoạn 2 (đã được xác nhận)

10. Tên danh mục unique theo utf8mb4_unicode_ci; product.business_id nullable.
11. FK RESTRICT ở DB và passive_deletes='all' ở ORM; không cascade xóa lịch sử.
12. Role/status dùng VARCHAR + CHECK để dễ mở rộng bằng migration có kiểm soát.
13. Giá và tổng dòng được CHECK tại MySQL; header totals và state transitions do
    service tương lai xử lý, không tự triển khai giao dịch trong giai đoạn 2.
14. Seed insert-only, tất cả stock=0; không tạo giao dịch, movement hay doanh thu giả.
    CLI Admin riêng, prompt ẩn, hash scrypt, không có tài khoản mặc định.
15. Bảo vệ stage1_probe và các bảng reflected ngoài metadata khi autogenerate.
16. Test integration bằng MySQL Docker riêng, không reset DB, không drop_all;
    giữ dữ liệu test có mã ngẫu nhiên trong volume test riêng.
17. Set session MySQL UTC và ẩn SQL parameters trong exception/log. Giữ stack tách
    routes/services/models/templates như giai đoạn 1. Dừng chờ duyệt trước giai đoạn 3.

## Giai đoạn 3 (đã được xác nhận)

18. Flask-Login + Flask-WTF; giữ schema/migration giai đoạn 2. AuditLog lưu các
    sự kiện auth và bộ đếm đăng nhập sai bằng HMAC, không lưu identity/password.
19. Dùng MySQL GET_LOCK trên connection riêng để giới hạn sai 5 lần/15 phút có
    hiệu lực giữa workers, kèm limiter POST theo IP ở Nginx. Không thêm Redis.
20. Admin/Staff kiểm tra ở backend; quyền user được tải lại ở mỗi request.
    `/admin` chỉ là trang thông tin phạm vi quyền, không triển khai quản lý user.
21. Bootstrap 5.3.8 và Bootstrap Icons 1.13.1 lưu nội bộ kèm license; CSP không
    unsafe-inline/unsafe-eval. Dashboard không có KPI khi chưa có truy vấn nghiệp vụ.
22. Browser verification dùng Playwright tùy chọn trên host và UI profile riêng
    nối DB test. Không tạo tài khoản hoặc mật khẩu demo mặc định.
23. Tách commit nền tảng/database giai đoạn 1–2 và commit auth/layout giai đoạn 3
    theo yêu cầu commit/push của người dùng. Push cần URL remote đích; không sửa
    Git global. Dừng trước giai đoạn 4.

## Refactor Giai đoạn 3 — hai không gian làm việc

24. Admin và Staff có Dashboard/layout/menu riêng; kế thừa workspace shell và
    navigation macro để tránh trùng auth, Logout, topbar và responsive.
25. Giữ alias `/dashboard` theo role và `/admin` chỉ Admin; đăng nhập về trang chủ
    role, next có allowlist chặt. Chính sách ban đầu chặn chéo hai Dashboard đã
    được thay bằng quyết định 28 bên dưới. Không đổi role trong database.
26. Admin ưu tiên thông tin tài khoản/ma trận quyền chỉ xem, trạng thái MySQL dùng
    SELECT 1 thật. Staff ưu tiên bố cục nghiệp vụ và shortcut không tương tác khi
    chưa triển khai, không dựng KPI, giao dịch hoặc cảnh báo giả.
27. Dùng CSS workspace riêng, sidebar 244/80px, scrollbar mảnh, offcanvas mobile;
    không đổi assets/framework. So sánh SHA-256 từng bảng trước/sau, kể cả users,
    audit_logs, stage1_probe và alembic_version. Không seed lại demo.

28. Theo điều chỉnh quyền của người dùng, Admin được cả Admin và Business;
    Staff chỉ Business. business_required dùng allowlist admin/staff, còn
    admin_required chỉ admin. Login mặc định giữ theo role. Menu chuyển workspace
    không đổi session/role và không yêu cầu login lại. Business vẫn dùng layout
    riêng; vai trò hiển thị lấy từ current_user, không suy ra từ layout.

## Giai đoạn 4 — dữ liệu kinh doanh

29. Theo yêu cầu mới, Admin và Staff đều có CRUD danh mục/nhà cung cấp/sản phẩm.
    Quyền này thay phần Staff chỉ xem của đặc tả gốc trong ba module; đã báo cáo
    khác biệt trước khi lập trình. Admin workspace vẫn chỉ Admin.
30. Kiểm tra schema cho thấy businesses chỉ là nhà cung cấp, không có cột loại
    đối tác. Dùng nguyên ba bảng và các FK/unique/index hiện có; không migration mới.
31. Ba Blueprint dùng bộ route/template chung qua catalog/resources.py; transaction
    ghi dữ liệu nằm trong catalog_service. Form là whitelist trường cho phép ghi;
    stock_quantity không được nhận từ client và sản phẩm mới có tồn kho 0.
32. Audit create/update/delete và dữ liệu catalog commit cùng nhau. FK RESTRICT
    ngăn xóa bản ghi đã dùng; sản phẩm còn tồn kho cũng bị chặn với khóa hàng.
33. Ảnh dùng placeholder nội bộ và URL đã validation mở qua liên kết; không tải
    URL từ backend, không thêm external assets vào CSP, chưa có upload ảnh.
34. Giai đoạn 3 commit/push riêng tại 09e9c4b, xác minh remote main. Giai đoạn 4
    để uncommitted cho người dùng duyệt; không triển khai Giai đoạn 5 hoặc AWS.

35. Đợt hoàn thiện UI/UX: người dùng xác nhận riêng cho phép preview ảnh HTTP/HTTPS
    bên ngoài ở trang sản phẩm. Thay phần chỉ liên kết của quyết định 33: CSP chỉ
    mở img-src tại Blueprint products, các trang khác/script/style/font giữ self.
    Browser tải trực tiếp không referrer, không log URL, không server proxy;
    ảnh lỗi về SVG nội bộ. Không thêm upload hoặc thay schema.
36. Nhóm field/microcopy dùng metadata Resource và macro chung cho create/edit/detail.
    Danh mục tạo mới có placeholder bắt buộc, sửa giữ giá trị cũ. Giá không format
    hoặc làm tròn trên client; chỉ bổ sung hướng dẫn nhập. Seed và tồn kho giữ nguyên.

37. Đợt tinh chỉnh cuối thay phần nhập giá của quyết định 36: progressive enhancement
    tạo ô hiển thị Việt Nam và giữ trường chuẩn có name gốc cho backend Decimal.
    Dấu chấm nhóm nghìn, dấu phẩy thập phân; chuyển bằng chuỗi, không số thực,
    không làm tròn. Không JS dùng form number nguyên bản. Không thay schema,
    API form POST, URL, quyền truy cập, dashboard hoặc kích thước toàn bộ UI.

38. Giai đoạn 6 giữa kỳ triển khai trên feature/stage-6-dashboard, không triển khai
    Giai đoạn 5. Business Dashboard truy vấn catalog/tồn kho thật; Admin Dashboard
    hệ thống và chuyển workspace giữ nguyên. Staff xem 4 KPI số lượng; tổng giá
    trị tồn kho chỉ Admin, được kiểm tra ở service/backend, không chỉ ẩn menu.
39. Giá trị tồn kho SUM(stock_quantity * purchase_price) gồm cả inactive còn hàng,
    dùng Decimal; biểu đồ/cảnh báo chỉ products active. Recent gồm mọi trạng thái
    vì quyền catalog hiện tại cho cả hai role xem inactive. Không doanh thu giả.
40. Sáu SELECT trong snapshot đọc mới; top 8 danh mục và nhóm còn lại, 8 cảnh báo,
    6 recent. Dùng Chart.js 4.5.1 UMD/MIT nội bộ và bảng HTML fallback; không CDN,
    CSP mới, API mới hoặc migration/index khi chưa có số liệu tải chứng minh cần.

41. Giai đoạn 6 commit dc0d7be, main fast-forward/push theo xác nhận người dùng;
    Giai đoạn 5 phát triển trên feature/stage-5-inventory-sales, chờ nghiệm thu.
42. Admin quản lý nhập kho và toàn bộ giao dịch; Staff chỉ đơn bán do mình tạo,
    hủy draft, xem movement của đơn đó. Chưa cấp Staff nhập kho, hủy completed
    hoặc quyền hệ thống. Không thay quyền CRUD catalog đã nghiệm thu.
43. Session ghi riêng với begin/commit/rollback, khóa document rồi product theo
    ID tăng dần. Không sửa/xóa giao dịch hoặc movement, không giữ chỗ draft.
    Mã có UNIQUE, ticket ký gắn actor/kind/code chống gửi cùng form hai lần.
44. Đảo nhập completed dùng adjustment/reference purchase_receipt và lý do cố
    định, không đổi schema/CHECK. Không thay purchase_price catalog khi nhập,
    không tính giá vốn/lợi nhuận hoặc thêm báo cáo doanh thu trong đợt này.

45. Giai đoạn 5.1 được người dùng duyệt: UNIQUE phone chuẩn hóa +84, gồm cả
    inactive. Không gộp theo tên/phone hoặc tự liên kết đơn cũ; vãng lai luôn NULL.
46. Staff có projection lịch sử completed của khách toàn cửa hàng để tư vấn,
    không notes/audit, không link/quyền mở đơn khác owner. Admin quản lý hồ sơ;
    Staff chỉ tạo khách mới trong transaction lập đơn, không sửa/vô hiệu hóa.
47. Thêm customer_id nullable nhưng giữ bốn trường snapshot độc lập. Chọn khách
    thì backend đọc lại hồ sơ active, không tin thông tin tự điền. Tạo khách
    mới + draft/items/audit cùng transaction; UNIQUE xử lý trùng đồng thời.
48. Migration additive c051_customers kiểm thử empty/legacy và backup restore
    trước demo. Chặn downgrade tự động vì mất hồ sơ/liên kết; rollback app giữ
    schema tương thích, recovery/forward fix phải được duyệt riêng. Không AWS.

49. 5.2 được duyệt: snapshot chính sách lúc tạo draft, bắt đầu từ completed_at
    thực tế theo ngày Việt Nam; cộng tháng lịch và còn hạn hết ngày kết thúc.
    Không suy đoán chính sách hoặc thời điểm hoàn tất cho đơn cũ.
50. Thêm warranty_devices ngoài coverage/ticket/event để MySQL UNIQUE bảo vệ
    serial và (coverage,unit_index). Tạo thiết bị theo nhu cầu, không sinh theo
    toàn bộ số lượng bán. Phiếu open có generated device key UNIQUE.
51. Còn hạn không cam kết miễn phí: phải có kết quả kiểm tra trước khi chấp nhận.
    Từ chối phải ghi lý do. Hoàn thành/từ chối vẫn giữ thiết bị đến khi trả khách.
52. Staff tra cứu completed tối thiểu toàn cửa hàng nhưng chỉ xử lý phiếu mình
    tạo/được phân công. Chính sách, legacy verification và assignment Admin-only.
53. Nhận/xử lý bảo hành và hủy đơn dùng chung order lock đầu tiên; không đổi kho
    từ module bảo hành. Hủy đơn completed bị chặn khi còn phiếu chưa trả khách.
54. Giữ native details/summary cho menu Business để bàn phím/no-JS hoạt động;
    route con tự mở nhóm, không gộp Admin/Business hoặc thay URL cũ.

## Chuẩn bị production/AWS (được người dùng xác nhận ngày 2026-10-11)

55. Giữ Docker Compose local nguyên trạng. Production dùng EC2 + Amazon RDS for
    MySQL; database không public và chỉ security group EC2 được vào cổng 3306.
    Đây là lựa chọn bổ sung theo yêu cầu mới, thay hướng dẫn MVP cũ dùng MySQL
    container trên cùng EC2.
56. GitHub Actions chạy bộ test Docker biệt lập trên pull request. Sau khi AWS,
    DNS/HTTPS và GitHub variables sẵn sàng, push main có thể build image bất biến
    vào ECR, tải Compose/Nginx deployment bundle vào S3 và gọi EC2 qua SSM.
    GitHub xác thực bằng OIDC; không lưu AWS access key dài hạn.
57. Production migration là bước deploy có kiểm soát; không seed demo. Secrets
    ứng dụng và RDS chỉ nằm trên EC2 trong file quyền hạn chế, không trong Git,
    image hoặc workflow logs.
58. Domain chưa có; không bật AWS_DEPLOY_ENABLED hoặc tạo tài nguyên thật trong
    bước chuẩn bị. Public login chỉ được mở sau khi DNS và HTTPS hoạt động.
    Người dùng hiện có $100 credit nhưng cần xác nhận thời hạn/điều kiện và xem
    ước tính chi phí trước khi tạo EC2/RDS/ECR/S3.
