# TechFlow — Nghiệm thu cuối Giai đoạn 5

Ngày 10/10/2026. Branch `feature/stage-5-inventory-sales`.
Người dùng cho phép commit/push branch khi các kiểm tra đạt; không merge main.

## Luồng nghiệp vụ trên MySQL test riêng

Bổ sung `test_acceptance_purchase_sale_return_ledger` trong `tests/test_inventory.py`.
Mỗi bước kiểm tra số tồn và toàn bộ quantity_delta của sản phẩm fixture:

| Thao tác | Tồn | Lịch sử delta |
| --- | ---: | --- |
| Tạo nhập draft 5 | 0 | Chưa có |
| Xác nhận nhập | 5 | +5 |
| Tạo bán draft 4 | 5 | +5 |
| Xác nhận bán | 1 | +5, -4 |
| Hủy phiếu nhập khi thiếu tồn | 1 | +5, -4, không thêm movement |
| Hủy đơn bán completed | 5 | +5, -4, +4 |
| Hủy phiếu nhập completed | 0 | +5, -4, +4, -5 |
| Hủy lại từng giao dịch | 0 | Bị từ chối, không thêm movement |

Loại movement lần lượt là purchase_in, sale_out, sale_return, adjustment.
Hủy nhập thất bại giữ phiếu ở completed. Test này đạt trên MySQL 8 Docker.

## Regression, quyền và giao diện

- 225 bài regression backend đạt trong 52.24 giây; bài nghiệm thu bổ sung đạt
  riêng, tổng cộng 226 bài backend đạt. Bao gồm rollback sau flush, 5 tình huống
  cạnh tranh service và hai HTTP request bán đồng thời, Decimal, CSRF và login.
- Staff không vào nhập kho hoặc Admin Dashboard; không xem/xác nhận đơn của
  người khác. Danh sách và phân trang scope theo owner. Lịch sử Staff chỉ thuộc
  đơn của mình; Admin quản lý toàn bộ. Hủy completed chỉ Admin.
- Playwright giao dịch đạt 6 tổ hợp Admin/Staff × desktop/tablet/mobile và
  một luồng tạo draft không JavaScript. Đã xem ảnh form nhập desktop/mobile:
  không tràn ngang, giữ bố cục/design system hiện có, không sửa CSS trong lượt này.
- Dashboard đạt 6 tổ hợp, 2 trường hợp lỗi thư viện chart, 2 trường hợp no-JS.
  Lần đầu bị lệch KPI vì người thực hiện chạy chồng với bộ test giao dịch đang
  cập nhật stock test; chạy lại tuần tự đạt, không thay assertion hoặc code KPI.
- Bộ workspace ban đầu gặp HTTP 429 khi các suite đăng nhập liên tiếp vượt
  ngân sách Nginx 10 lần/phút, burst 5. Giữ nguyên limiter, giãn thời gian giữa
  các suite khi chạy lại; không tắt bảo vệ hoặc đổi mật khẩu/tài khoản demo.
- Lượt chạy lại workspace đạt đủ 6 tổ hợp vai trò/kích thước màn hình. Catalog
  đạt 6 tổ hợp, 18 chu trình CRUD, 72 kiểm tra POST/loading; giá gửi từ form
  khớp DECIMAL trong MySQL. Bộ filter/paging/profile đạt 18 luồng và kiểm tra
  no-JS CRUD/độ chính xác giá/validation. Không có lỗi chức năng còn tái hiện.

## Bảo vệ dữ liệu và Git

Snapshot chỉ đọc `.docker-local/stage5-acceptance-before.json` giữ local, không
vào Git. Đối chiếu row count/SHA-256 cả 12 bảng demo đạt; giữ nguyên tài khoản,
stage1_probe, migration và tất cả dữ liệu. check-db đạt; Alembic vẫn
`db55d828848e (head)`. Không chạy migration hoặc seed database demo.

Đã xem status/diff, kiểm tra diff --check và compileall. Scan Git-visible files
với secret local trong bộ nhớ và mẫu private key/AWS key không phát hiện secrets;
không in giá trị secret. .env, .venv, cache, snapshot và ảnh test sinh tự động
được ignore; không đưa database/volume/file tạm vào commit. Ảnh đã track từ các
giai đoạn trước giữ nguyên. Fetch xác nhận main vẫn `dc0d7be`, remote chưa có
branch Giai đoạn 5 trước push. Không force/reset/merge main.
Tổng cộng 41 file được chọn vào commit; ảnh minh chứng vẫn chỉ lưu local.

Các giới hạn nghiệp vụ giữ nguyên trong [STAGE_5_REPORT.md](STAGE_5_REPORT.md):
chưa sửa draft, cấp quyền nhập riêng cho Staff, điều chỉnh kho thủ công, giá vốn
hoặc báo cáo doanh thu nâng cao. Chưa kiểm thử tải lớn/thiết bị vật lý và browser
ngoài Chromium. Không triển khai AWS hoặc giai đoạn tiếp theo.
