# Đề xuất Cài đặt hệ thống TechFlow

Đây là phương án cho đợt phát triển sau, chưa có route, form lưu, bảng cấu hình
hoặc quyền mới. Đợt UI/UX trước Giai đoạn 7 chỉ bổ sung tài liệu này.

| Nhóm | Dữ liệu hiện có | Hướng mở rộng cần duyệt |
| --- | --- | --- |
| Quy ước hiển thị | VND, ngày giờ Asia/Ho_Chi_Minh, timestamps UTC | Ban đầu chỉ xem quy ước đang áp dụng; thay đổi cần đánh giá toàn ứng dụng |
| Tài khoản và phân quyền | Hai role và ma trận quyền backend | Chỉnh tài khoản/role phải là chức năng riêng có authorization, validation và audit |
| Chính sách bảo hành | Cấu hình từng sản phẩm, snapshot theo dòng bán | Thư viện chính sách dùng chung, phiên bản và áp dụng cho đơn mới; không sửa snapshot cũ |
| Trạng thái hệ thống | Kiểm tra kết nối web/MySQL trên Dashboard Admin | Có thể tổ chức lại thông tin chỉ đọc; không hiển thị secrets, URL kết nối hoặc biến môi trường thô |
| Thông tin cửa hàng | Chưa có nơi lưu hồ sơ cửa hàng | Đề xuất tên, thông tin liên hệ, địa chỉ; cần thiết kế lưu trữ riêng, không dùng bảng nhà cung cấp |

Nếu triển khai, đặt trong workspace Admin, kiểm tra quyền backend; Staff không
quản lý cấu hình. Chỉ đưa mục vào menu khi có nội dung thật và route hoạt động.
Không có nút Lưu cho dữ liệu chỉ đọc; không thêm placeholder tương tác.

Thư viện bảo hành tương lai cần phân biệt mẫu chính sách và chính sách đã bán.
Việc đổi mẫu chỉ tác động giao dịch mới theo quy tắc được duyệt; không suy đoán
chính sách đơn cũ hoặc đồng nhất còn hạn với miễn phí. Cần migration và kế hoạch
kiểm thử riêng, không thực hiện trong đợt tinh chỉnh giao diện này.

Không đề xuất chi nhánh, thuế, công nợ, cổng thanh toán hoặc tài nguyên cloud
trong phạm vi hiện tại. Bảo mật/vận hành vẫn do cấu hình môi trường và quy trình
triển khai quản lý; không đưa secrets vào trang Cài đặt.
