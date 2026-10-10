# Giai đoạn 5 — kế hoạch và quy tắc

Baseline Giai đoạn 6: `dc0d7be96ab5217bf8cd7c978c8669918cc7b4b6`.
Đã chạy lại 165 backend tests (49.09s) và 6 Dashboard browser flows + 4 fallback/no-JS,
commit đúng message được yêu cầu, fetch xác nhận remote không có thay đổi mới,
fast-forward/push main không force. Local main/remote main cùng hash trên.
Branch phát triển: `feature/stage-5-inventory-sales`. Không commit/push Giai đoạn 5
trước nghiệm thu. Screenshot Giai đoạn 6 giữ local theo .gitignore.

## Ma trận quyền backend

| Chức năng | Admin | Staff |
| --- | --- | --- |
| Hai Dashboard và catalog | Giữ nguyên quyền hiện tại | Business/catalog như Giai đoạn 4/6 |
| Nhập kho: xem/tạo/xác nhận/hủy | Tất cả | Không được cấp quyền nhập kho |
| Đơn bán: xem/tạo/xác nhận | Tất cả | Chỉ đơn do chính mình tạo |
| Hủy đơn draft | Tất cả | Chỉ đơn do chính mình tạo |
| Hủy đơn completed | Có | Không |
| Lịch sử kho | Tất cả | Chỉ movement từ đơn bán của mình |
| Sửa/xóa movement; xóa giao dịch | Không có route | Không có route |

Đặc tả cho phép Staff nhập kho **nếu được cấp quyền**; schema chỉ có role nên MVP
chưa cấp quyền đó. Không mở rộng quyền quản trị hệ thống cho Staff. Quyền được kiểm
tra lại trong service khi ghi; danh sách/detail/history được scope trước pagination.

## State machine

| Từ | Thao tác | Đến | Kho |
| --- | --- | --- | --- |
| — | Tạo | draft | Không đổi; giá snapshot, tổng do backend tính |
| draft | Xác nhận | completed | Nhập +qty / bán -qty |
| draft | Hủy | cancelled | Không đổi |
| completed | Hủy (Admin) | cancelled | Đảo lượng đúng một lần |
| completed | Xác nhận lại | Từ chối | Không đổi |
| cancelled | Bất kỳ xử lý lại | Từ chối | Không đổi |

Không sửa dòng/xóa phiếu qua UI. Hủy phiếu nhập completed bị chặn nếu bất kỳ sản
phẩm nào thiếu kho. Đảo phiếu nhập dùng movement `adjustment`, reference
`purchase_receipt`, delta âm và lý do rõ ràng; khớp CHECK constraint hiện có.
Không tự thay purchase_price khi nhập; unit_cost là snapshot phiếu, giá trị tồn
kho Dashboard vẫn là ước tính theo giá mua hiện tại của catalog.

## Trình tự

1. Service transaction/state/permission và primitive stock/Decimal.
2. Phiếu nhập, form nhiều dòng, confirm/cancel và test riêng module.
3. Đơn bán, giá snapshot/stock validation/ownership và test riêng module.
4. Lịch sử append-only chỉ đọc, link giao dịch, lọc/phân trang theo quyền.
5. MySQL rollback, race thực với connection riêng, tiền chính xác, chống lặp.
6. Dashboard phản ánh kho thật, full regression và Playwright 3 viewport, tài liệu.

Schema hiện có đủ trường/FK/unique/CHECK/index, dự kiến không migration. Nếu phát
sinh nhu cầu thay đổi sẽ mô tả tương thích trước khi áp dụng. Test nghiệp vụ chỉ
dùng `techflow_test`/`db-test`/volume test riêng. Main giữ snapshot fingerprint
`.docker-local/stage5-before.json`, không seed/reset/thay đổi account hoặc secrets.
