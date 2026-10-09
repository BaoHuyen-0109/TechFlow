# Xử lý Docker Desktop trên Windows

## Kết quả kiểm tra ngày 09/10/2026

- **Cập nhật:** người dùng đã mở Docker Desktop. Client/Server kết nối thành công;
  ba service TechFlow healthy, MySQL kết nối được và dữ liệu giữ nguyên qua restart.
  Các lỗi Engine bên dưới là lịch sử chẩn đoán trước khi Docker Desktop chạy.
- Docker CLI 29.6.2, Compose v5.3.1 đã có.
- Kiểm tra ngoài sandbox: context `desktop-linux`, pipe
  `dockerDesktopLinuxEngine` không tồn tại; chưa kết nối được Engine.
- WSL mặc định Ubuntu, phiên bản 2.
- Trong sandbox, đọc `.docker/config.json` và trạng thái WSL bị từ chối quyền;
  không kết luận file cấu hình hỏng từ lỗi sandbox này.
- Python 3.12.7 có ở Anaconda khi kiểm tra ngoài sandbox.

## Những bước người dùng cần thực hiện

1. Mở Docker Desktop từ Start Menu, chờ Engine running. Chọn Linux containers
   nếu đang dùng Windows containers. Trong Settings kiểm tra backend WSL 2.
2. Mở PowerShell của chính tài khoản Dell, chạy:

```powershell
docker context ls
docker --context desktop-linux version
docker compose version
wsl --status
```

`docker version` cần có cả Client và Server. Nếu context desktop-linux có sẵn nhưng
chưa là context đang dùng, có thể chọn bằng `docker context use desktop-linux`.
Không đổi context nếu đang cố ý làm việc với engine khác.

3. Nếu Engine vẫn không lên, xem thông báo trong Docker Desktop → Troubleshoot,
   thử Restart Docker Desktop sau khi lưu công việc container đang chạy.
4. Nếu WSL/virtualization báo lỗi, kiểm tra Windows features WSL/Virtual Machine
   Platform và virtualization BIOS theo thông báo thực tế. Việc cài/cập nhật WSL
   hoặc reboot do người dùng quyết định; không thực hiện reset/xóa distro hay factory reset.
5. Nếu `config.json: Access is denied` vẫn xuất hiện ở PowerShell cá nhân ngoài
   sandbox, kiểm tra owner/quyền đọc file với quản trị viên; không in nội dung config
   vì có thể chứa thông tin đăng nhập registry, không cấp quyền Everyone.

Khi Server đã phản hồi, thực hiện README. Image build cần Internet để tải base images
và Python dependencies. Không có kết nối Engine thì không thể xác nhận build, container
health, Nginx proxy, MySQL kết nối hoặc tính bền vững của volume.

## Lỗi thường gặp khi chạy project

- Thiếu biến môi trường: điền `.env`, không dùng `.env.example` với secret trống.
- Port 8000 bận: đổi APP_PORT trong `.env` rồi recreate Nginx.
- DB unhealthy: xem `docker compose logs db` tại máy; không đăng log chứa secrets.
- Đổi password trong `.env` không đổi user đã nằm trong volume MySQL. Dùng quy trình
  đổi mật khẩu có kiểm soát; không xóa volume để sửa lỗi kết nối.
- `check-db` thất bại: kiểm tra DB healthy, tên DB/user, host `db` trong container.
