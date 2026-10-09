# Quy ước làm việc nhóm

## Nhánh và review

- `main`: phiên bản đã kiểm thử, sẵn sàng demo. Không push trực tiếp khi nhóm bắt đầu cộng tác.
- Tạo nhánh ngắn từ main: `feat/auth`, `feat/products`, `feat/purchases`, `fix/db-config`, `docs/setup`.
- Mỗi PR giải quyết một thay đổi rõ ràng, ghi hành vi, cách kiểm thử, migrations và giới hạn.
- Có ít nhất một thành viên review trước khi merge. Dùng squash merge nếu nhóm thống nhất.
- Remote GitHub chưa được tạo/cấu hình. Trưởng nhóm tạo repository rồi thêm remote;
  không đưa token vào URL, source hoặc tài liệu.

```powershell
git switch main
git pull --ff-only
git switch -c feat/ten-module
# Thực hiện thay đổi và chạy tests
git status
git diff
git add app tests docs
git commit -m "feat(products): thêm bộ lọc danh mục"
git push -u origin feat/ten-module
```

Lệnh pull/push cần remote do trưởng nhóm cấu hình. Chưa có commit đầu tiên thì
thực hiện commit nền tảng sau khi review, trước khi chia nhánh.

## Quy ước code

- Python: PEP 8, 4 spaces, snake_case cho hàm/module, PascalCase cho class,
  type hints ở service/config khi phù hợp. Không thêm tầng repository khi chưa cần.
- Route/Blueprint, form, service, model, template tách rõ. Validation luôn ở backend.
- Mọi thao tác ghi dùng POST + CSRF + permission check; GET không thay đổi dữ liệu.
- Nội dung hiển thị tiếng Việt; tên biến/module tiếng Anh. Template tự escape dữ liệu.
- Secrets chỉ trong môi trường hoặc `.env` bị ignore. Không gửi `.env` qua PR/chat.
- Thay đổi schema luôn kèm migration. Nhóm kiểm tra nhiều Alembic heads trước merge;
  không sửa migration đã được các thành viên áp dụng, không chạy reset DB để xử lý conflict.
- Models mua/bán và nghiệp vụ kho là phần cuối kỳ: transaction, khóa hàng, audit và
  chống xác nhận lặp phải có test MySQL trên database test riêng trước khi tích hợp.
- Cập nhật README và docs theo hành vi thực tế, không đánh dấu test chưa chạy là thành công.

## Commit

Ví dụ: `feat(auth): thêm đăng nhập`, `fix(config): xử lý ký tự đặc biệt`,
`test(products): kiểm tra SKU trùng`, `docs: bổ sung hướng dẫn Docker`.

Trước merge: chạy test liên quan, kiểm tra `git diff --check`, review file staged
để tránh secrets/dump/key, ghi kết quả kiểm thử trong PR. Không force-push main.

## Git ownership trên máy hiện tại

Repository được khởi tạo bởi tài khoản sandbox. Khi chạy Git bằng tài khoản Dell,
có thể gặp `detected dubious ownership`. Chỉ với workspace E:\AWS do bạn kiểm soát,
có thể dùng exception giới hạn cho từng lệnh:

```powershell
git -c safe.directory=E:/AWS status
git -c safe.directory=E:/AWS diff
```

Hoặc tự thêm đúng đường dẫn này vào cấu hình cá nhân nếu muốn áp dụng lâu dài:
`git config --global --add safe.directory E:/AWS`. Không dùng wildcard `*`.
Agent chưa sửa cấu hình Git global, chưa tạo commit hoặc remote.
