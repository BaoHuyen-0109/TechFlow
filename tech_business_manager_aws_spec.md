# ĐẶC TẢ DỰ ÁN --- WEBSITE QUẢN LÝ KINH DOANH THIẾT BỊ CÔNG NGHỆ

## Docker + Amazon EC2 + AWS

> **Tên đề tài:** Nghiên cứu và triển khai Website quản lý kinh doanh
> thiết bị công nghệ sử dụng Docker và Amazon EC2 trên nền tảng AWS\
> **Mục đích tài liệu:** Đây là đặc tả tổng thể để đưa cho AI coding
> agent / người lập trình xây dựng dự án theo từng giai đoạn. Đọc toàn
> bộ tài liệu trước khi code, tuân thủ các quyết định kiến trúc và tiêu
> chí nghiệm thu bên dưới.\
> **Ngôn ngữ giao diện:** Tiếng Việt.\
> **Đối tượng sử dụng:** Chủ cửa hàng / quản trị viên và nhân viên kho,
> bán hàng.\
> **Định hướng:** Ứng dụng có thể chạy local bằng Docker Compose, sau đó
> triển khai lên một Amazon EC2 instance. Ưu tiên đơn giản, an toàn, dễ
> demo và kiểm soát chi phí.

------------------------------------------------------------------------

# 1. Hướng dẫn dành cho AI coding agent

Hãy thực hiện dự án theo từng giai đoạn, không sinh toàn bộ mã nguồn một
cách thiếu kiểm soát.

## 1.1. Quy tắc làm việc bắt buộc

1.  Trước khi code, hãy tạo kế hoạch triển khai và cấu trúc thư mục đề
    xuất.
2.  Ưu tiên mã nguồn rõ ràng, dễ đọc, có type hints khi phù hợp, tách
    route/controller, service, model và template.
3.  Không hardcode mật khẩu, secret key, thông tin AWS, địa chỉ IP hoặc
    thông tin database thật trong mã nguồn.
4.  Tạo `.env.example`; không commit `.env`.
5.  Dùng migration để quản lý thay đổi schema; không dựa vào việc tự tạo
    bảng ở production.
6.  Tạo dữ liệu mẫu có thể nạp lại bằng seed script; không seed tự động
    mỗi lần khởi động production.
7.  Tất cả thao tác thay đổi dữ liệu phải được kiểm tra dữ liệu đầu vào
    ở backend.
8.  Sử dụng truy vấn có tham số hoặc ORM; không nối chuỗi input của
    người dùng vào SQL.
9.  Thêm xử lý lỗi thân thiện và logging; không hiển thị stack trace
    hoặc secret cho người dùng.
10. Bảo đảm các thao tác ghi dữ liệu liên quan (ví dụ tạo phiếu nhập và
    cập nhật tồn kho) dùng transaction.
11. Mọi trang cần có trạng thái loading, empty state, lỗi và thông báo
    thành công phù hợp.
12. Viết README đầy đủ để một người mới có thể chạy local và triển khai
    AWS theo hướng dẫn.
13. Không tuyên bố một dịch vụ AWS "miễn phí" nếu chưa kiểm tra điều
    kiện tài khoản, khu vực và chương trình credit hiện tại.
14. Không tự động tạo tài nguyên AWS, không chạy lệnh có thể gây phát
    sinh phí hoặc xóa dữ liệu khi chưa được người dùng xác nhận.
15. Nếu gặp quyết định chưa được chỉ định, ưu tiên giải pháp ít thành
    phần, chi phí thấp, dễ vận hành; ghi lại quyết định trong
    `docs/DECISIONS.md`.

## 1.2. Các giai đoạn thực hiện

-   **Giai đoạn 1:** Khởi tạo repository, cấu hình, Docker Compose và
    kết nối database.
-   **Giai đoạn 2:** Models, migrations, seed data và kiểm thử database.
-   **Giai đoạn 3:** Đăng nhập, phân quyền và layout chung.
-   **Giai đoạn 4:** CRUD doanh nghiệp/nhà cung cấp, danh mục, sản phẩm.
-   **Giai đoạn 5:** Nhập kho, đơn bán hàng và cập nhật tồn kho bằng
    transaction.
-   **Giai đoạn 6:** Dashboard, tìm kiếm, lọc, phân trang và báo cáo.
-   **Giai đoạn 7:** Kiểm thử, hardening bảo mật, logging và tài liệu.
-   **Giai đoạn 8:** Docker production và triển khai lên EC2.
-   **Giai đoạn 9:** Kiểm thử nghiệm thu, ghi lại số liệu thực nghiệm
    cho báo cáo Cloud Computing.

Sau mỗi giai đoạn, chạy test liên quan, báo cáo file đã tạo, lệnh chạy
và các vấn đề còn tồn tại. Không chuyển giai đoạn nếu phần cốt lõi của
giai đoạn trước chưa hoạt động.

------------------------------------------------------------------------

# 2. Tổng quan sản phẩm

## 2.1. Bối cảnh

Xây dựng website nội bộ cho một cửa hàng kinh doanh thiết bị công nghệ.
Cửa hàng nhập hàng từ các nhà cung cấp, quản lý danh mục và thông số sản
phẩm, theo dõi tồn kho, lập đơn bán hàng và xem số liệu hoạt động.

Dữ liệu doanh nghiệp trong demo là dữ liệu giả lập. Không sử dụng thông
tin cá nhân hoặc dữ liệu kinh doanh thật khi seed database.

## 2.2. Mục tiêu

-   Quản lý tập trung sản phẩm, danh mục và nhà cung cấp.
-   Theo dõi nhập kho, xuất kho và tồn kho.
-   Quản lý đơn bán hàng ở mức cơ bản.
-   Hỗ trợ dashboard và báo cáo nhanh.
-   Chạy nhất quán trên máy lập trình và máy chủ thông qua Docker.
-   Có thể triển khai ứng dụng trên Amazon EC2.
-   Có các cấu hình cần thiết cho bảo mật, logging, sao lưu và theo dõi
    chi phí.
-   Tạo nền tảng thực nghiệm để đánh giá hiệu năng và khả năng vận hành
    của ứng dụng trên Cloud.

## 2.3. Ngoài phạm vi phiên bản đầu

Không triển khai trong MVP trừ khi được yêu cầu rõ ràng:

-   Thanh toán online hoặc tích hợp cổng thanh toán.
-   Hóa đơn điện tử, kế toán và thuế thực tế.
-   Đồng bộ tồn kho đa chi nhánh.
-   Tích hợp ERP, CRM hoặc hệ thống bên thứ ba.
-   Microservices/Kubernetes.
-   Tự động mở rộng nhiều EC2 hoặc kiến trúc multi-region.
-   Upload ảnh trực tiếp lên S3 (phiên bản đầu có thể dùng URL ảnh hoặc
    ảnh mặc định).
-   Đa ngôn ngữ.
-   Ứng dụng mobile native.

------------------------------------------------------------------------

# 3. Công nghệ và kiến trúc

## 3.1. Stack được chọn

Dùng stack sau cho MVP để giảm độ phức tạp triển khai:

  -----------------------------------------------------------------------
  Lớp                     Công nghệ               Vai trò
  ----------------------- ----------------------- -----------------------
  Frontend                HTML5, CSS3, Bootstrap  Giao diện responsive
                          5, JavaScript           

  Template                Jinja2                  Render trang phía
                                                  server

  Backend                 Python 3.12 + Flask     Routing, nghiệp vụ và
                                                  xác thực

  ORM                     Flask-SQLAlchemy /      Truy vấn database an
                          SQLAlchemy              toàn

  Migration               Flask-Migrate / Alembic Quản lý schema

  Database                MySQL 8.0               Dữ liệu nghiệp vụ

  Driver                  PyMySQL hoặc            Kết nối MySQL
                          mysqlclient             

  Auth                    Flask-Login             Session đăng nhập

  Form validation         Flask-WTF / WTForms     CSRF và validation form

  Password hashing        Werkzeug security hoặc  Hash mật khẩu
                          thư viện chuẩn tương    
                          đương                   

  Web server container    Gunicorn                Chạy Flask trong
                                                  production

  Reverse proxy           Nginx                   Public HTTP/HTTPS,
                                                  static files và reverse
                                                  proxy

  Container               Docker + Docker Compose Đóng gói và chạy nhiều
                                                  dịch vụ

  Cloud VM                Amazon EC2 Ubuntu LTS   Máy chủ triển khai

  Persistent storage      EBS volume gắn với EC2  Lưu dữ liệu MySQL và dữ
                                                  liệu cần giữ

  Monitoring (tùy chọn)   Amazon CloudWatch       Log và chỉ số máy chủ

  Source control          Git + GitHub            Quản lý mã nguồn
  -----------------------------------------------------------------------

**Kiến trúc MVP:** Monolithic Flask app + MySQL, chạy trong hai
container riêng; Nginx có thể là container thứ ba. Dùng Docker Compose.
Không cần React cho phiên bản đầu vì Jinja2 + Bootstrap đơn giản hơn,
phù hợp CRUD và triển khai trên một EC2.

## 3.2. Sơ đồ logic

``` text
Người dùng / Trình duyệt
        |
      HTTP/HTTPS
        |
   Security Group
        |
   EC2 (Ubuntu LTS)
        |
   Docker Compose network
        |
   +--------------------+
   | Nginx :80 / :443   |  <-- cổng public
   +--------------------+
        |
        v
   +--------------------+
   | Flask + Gunicorn   |  <-- chỉ nội bộ Docker network
   +--------------------+
        |
        v
   +--------------------+
   | MySQL 8            |  <-- chỉ nội bộ Docker network
   +--------------------+
        |
        v
   Docker named volume trên EBS
```

Trong local development có thể publish cổng Nginx ra `localhost`; không
publish cổng MySQL ra Internet. Trên EC2, chỉ mở cổng 80/443 cho website
và cổng 22 cho SSH có giới hạn IP nguồn. Không mở cổng 3306 công khai.

## 3.3. Quyết định database trên EC2

MVP dùng MySQL container trên cùng EC2 để giảm chi phí và làm rõ nội
dung Docker. Dữ liệu MySQL phải nằm trên persistent volume, không nằm
trong writable layer của container.

Giới hạn: một EC2 duy nhất là điểm lỗi đơn, không có high availability
mặc định. Với production thật, cân nhắc Amazon RDS for MySQL, backup tự
động, private networking và triển khai ứng dụng/database tách biệt. RDS
làm tăng chi phí nên không bắt buộc trong MVP.

------------------------------------------------------------------------

# 4. Vai trò và phân quyền

Có hai vai trò chính:

## 4.1. Admin

-   Xem dashboard.
-   CRUD người dùng.
-   CRUD danh mục, nhà cung cấp, sản phẩm.
-   Tạo và xem phiếu nhập kho.
-   Tạo và quản lý đơn bán hàng.
-   Xem báo cáo và nhật ký hoạt động.
-   Hủy đơn theo quy tắc nghiệp vụ.
-   Thay đổi trạng thái đơn hàng.
-   Không được xóa cứng dữ liệu đã được tham chiếu bởi giao dịch; dùng
    trạng thái inactive/soft delete khi cần.

## 4.2. Staff (nhân viên)

-   Xem dashboard giới hạn.
-   Xem sản phẩm, danh mục và nhà cung cấp.
-   Tạo phiếu nhập kho nếu được cấp quyền.
-   Tạo đơn bán hàng.
-   Xem danh sách giao dịch được phép.
-   Không quản lý người dùng hoặc cấu hình hệ thống.
-   Không được cấp quyền admin cho tài khoản khác.

MVP có thể bắt đầu bằng hai role `admin` và `staff`. Tất cả quyền phải
được kiểm tra tại backend, không chỉ ẩn nút trên frontend.

------------------------------------------------------------------------

# 5. Yêu cầu giao diện (UI/UX)

## 5.1. Phong cách

-   Giao diện quản trị hiện đại, gọn, chuyên nghiệp.
-   Tông màu trung tính; màu nhấn xanh dương hoặc xanh đậm.
-   Dùng Bootstrap 5, Bootstrap Icons hoặc icon set tương đương.
-   Sidebar trái trên desktop; chuyển thành offcanvas trên mobile.
-   Header có tên người dùng, role và nút đăng xuất.
-   Các bảng hỗ trợ tìm kiếm, lọc, phân trang và thao tác hàng.
-   Form có nhãn rõ ràng, lỗi validation ngay cạnh trường.
-   Dùng modal xác nhận khi xóa/hủy giao dịch.
-   Hiển thị toast/alert sau thao tác thành công hoặc thất bại.
-   Có trạng thái loading, empty state và error state.
-   Không dùng emoji làm icon giao diện chính.
-   Không để các nút "Sửa", "Xóa", "Thêm mới" bị tràn trên màn hình nhỏ.
-   Đảm bảo độ tương phản và điều hướng bằng bàn phím ở mức hợp lý.

## 5.2. Layout chung

-   `/login`: trang đăng nhập.
-   Layout quản trị gồm sidebar, topbar và content.
-   Dashboard là trang đầu tiên sau đăng nhập.
-   Mỗi trang CRUD có tiêu đề, breadcrumb, nút thêm mới và bảng dữ liệu.
-   Form thêm/sửa dùng chung template để tránh lặp code.
-   Dùng pagination phía server, không tải toàn bộ dữ liệu lớn lên trình
    duyệt.
-   Định dạng tiền Việt Nam bằng VND, ví dụ `12.500.000 ₫`.
-   Ngày giờ hiển thị theo múi giờ `Asia/Ho_Chi_Minh`; lưu timestamp
    nhất quán trong database.

## 5.3. Các trang cần có

1.  Login.
2.  Dashboard.
3.  Danh sách sản phẩm.
4.  Tạo/sửa/chi tiết sản phẩm.
5.  Danh sách danh mục.
6.  Danh sách nhà cung cấp/doanh nghiệp.
7.  Tạo/sửa/chi tiết nhà cung cấp.
8.  Danh sách phiếu nhập kho.
9.  Tạo phiếu nhập kho và chi tiết phiếu.
10. Danh sách đơn bán hàng.
11. Tạo đơn hàng và chi tiết đơn.
12. Chi tiết đơn hàng.
13. Danh sách người dùng (admin).
14. Nhật ký hoạt động.
15. Trang 403, 404, 500.
16. Health check endpoint dành cho monitoring.

------------------------------------------------------------------------

# 6. Mô hình dữ liệu MySQL

Dùng InnoDB, `utf8mb4` và collation phù hợp. Mọi bảng nghiệp vụ cần
primary key, timestamps và index hợp lý. Các trường tiền dùng `DECIMAL`,
không dùng FLOAT/DOUBLE. Số lượng phải là số nguyên không âm.

## 6.1. Bảng `users`

  -----------------------------------------------------------------------
  Cột                     Kiểu                    Quy tắc
  ----------------------- ----------------------- -----------------------
  id                      BIGINT UNSIGNED         PK, auto increment

  full_name               VARCHAR(120)            NOT NULL

  username                VARCHAR(80)             NOT NULL, UNIQUE

  email                   VARCHAR(190)            UNIQUE, có thể nullable
                                                  nếu chính sách cho phép

  password_hash           VARCHAR(255)            NOT NULL

  role                    ENUM('admin','staff')   NOT NULL
                          hoặc VARCHAR có         
                          validation              

  is_active               BOOLEAN                 NOT NULL, default true

  last_login_at           DATETIME nullable       Lần đăng nhập gần nhất

  created_at              DATETIME                NOT NULL

  updated_at              DATETIME                NOT NULL
  -----------------------------------------------------------------------

Không lưu password plaintext. Không trả về `password_hash` trong
response hoặc template.

## 6.2. Bảng `businesses` (nhà cung cấp)

  Cột              Kiểu              Quy tắc
  ---------------- ----------------- -----------------------------
  id               BIGINT UNSIGNED   PK
  code             VARCHAR(30)       UNIQUE, NOT NULL
  name             VARCHAR(180)      NOT NULL
  tax_code         VARCHAR(30)       nullable; nếu có thì unique
  contact_person   VARCHAR(120)      nullable
  email            VARCHAR(190)      nullable
  phone            VARCHAR(30)       nullable
  address          VARCHAR(255)      nullable
  notes            TEXT              nullable
  is_active        BOOLEAN           default true
  created_at       DATETIME          NOT NULL
  updated_at       DATETIME          NOT NULL

Tên giao diện: **Nhà cung cấp**. Trong báo cáo có thể mô tả đây là doanh
nghiệp cung cấp hàng hóa. Không giả định rằng website là hệ thống quản
lý mọi doanh nghiệp trên thị trường.

## 6.3. Bảng `categories`

  Cột           Kiểu              Quy tắc
  ------------- ----------------- ------------------
  id            BIGINT UNSIGNED   PK
  code          VARCHAR(30)       UNIQUE, NOT NULL
  name          VARCHAR(100)      NOT NULL
  description   TEXT              nullable
  is_active     BOOLEAN           default true
  created_at    DATETIME          NOT NULL
  updated_at    DATETIME          NOT NULL

Danh mục seed: Laptop, Linh kiện máy tính, Màn hình, Thiết bị ngoại vi,
Thiết bị mạng, Phụ kiện.

## 6.4. Bảng `products`

  -----------------------------------------------------------------------
  Cột                     Kiểu                    Quy tắc
  ----------------------- ----------------------- -----------------------
  id                      BIGINT UNSIGNED         PK

  sku                     VARCHAR(50)             UNIQUE, NOT NULL

  name                    VARCHAR(180)            NOT NULL

  category_id             BIGINT UNSIGNED         FK categories.id

  business_id             BIGINT UNSIGNED         FK businesses.id, nhà
                                                  cung cấp chính,
                                                  nullable nếu cho phép

  brand                   VARCHAR(100)            nullable

  model                   VARCHAR(100)            nullable

  description             TEXT                    nullable

  purchase_price          DECIMAL(14,2)           NOT NULL, \>= 0

  selling_price           DECIMAL(14,2)           NOT NULL, \>= 0

  stock_quantity          INT UNSIGNED            NOT NULL, default 0

  reorder_level           INT UNSIGNED            NOT NULL, default 5

  image_url               VARCHAR(500)            nullable

  is_active               BOOLEAN                 default true

  created_at              DATETIME                NOT NULL

  updated_at              DATETIME                NOT NULL
  -----------------------------------------------------------------------

Index: `sku` unique; index `name`; index `category_id`; index
`business_id`; index `is_active`. Có thể dùng tìm kiếm `LIKE` ở MVP.

Quy tắc: - SKU phải duy nhất. - Giá mua/giá bán không âm. -
`stock_quantity` không được âm. - Nếu sản phẩm đã xuất hiện trong giao
dịch, không xóa cứng; chuyển `is_active=false`. - `stock_quantity` là số
lượng hiện tại; phải được cập nhật trong transaction từ nghiệp vụ
nhập/xuất. - Không cho phép người dùng chỉnh sửa trực tiếp tồn kho tùy ý
trong form sản phẩm. Nếu cần điều chỉnh kho, tạo chức năng điều chỉnh
kho riêng có lý do và log.

## 6.5. Bảng `purchase_receipts` (phiếu nhập)

  Cột            Kiểu              Quy tắc
  -------------- ----------------- -------------------------------
  id             BIGINT UNSIGNED   PK
  receipt_code   VARCHAR(40)       UNIQUE
  business_id    BIGINT UNSIGNED   FK businesses.id
  created_by     BIGINT UNSIGNED   FK users.id
  receipt_date   DATETIME          NOT NULL
  status         VARCHAR(20)       draft / completed / cancelled
  total_amount   DECIMAL(14,2)     NOT NULL, default 0
  notes          TEXT              nullable
  created_at     DATETIME          NOT NULL
  updated_at     DATETIME          NOT NULL

## 6.6. Bảng `purchase_receipt_items`

  Cột          Kiểu              Quy tắc
  ------------ ----------------- -------------------------
  id           BIGINT UNSIGNED   PK
  receipt_id   BIGINT UNSIGNED   FK purchase_receipts.id
  product_id   BIGINT UNSIGNED   FK products.id
  quantity     INT UNSIGNED      NOT NULL, \> 0
  unit_cost    DECIMAL(14,2)     NOT NULL, \>= 0
  line_total   DECIMAL(14,2)     NOT NULL
  created_at   DATETIME          NOT NULL

Mỗi dòng có `line_total = quantity * unit_cost`. Tổng phiếu bằng tổng
các dòng. Backend tự tính, không tin giá trị total do browser gửi lên.

## 6.7. Bảng `sales_orders` (đơn bán hàng)

  Cột                Kiểu              Quy tắc
  ------------------ ----------------- -------------------------------
  id                 BIGINT UNSIGNED   PK
  order_code         VARCHAR(40)       UNIQUE
  customer_name      VARCHAR(150)      NOT NULL
  customer_phone     VARCHAR(30)       nullable
  customer_email     VARCHAR(190)      nullable
  customer_address   VARCHAR(255)      nullable
  created_by         BIGINT UNSIGNED   FK users.id
  order_date         DATETIME          NOT NULL
  status             VARCHAR(20)       draft / completed / cancelled
  total_amount       DECIMAL(14,2)     NOT NULL, default 0
  notes              TEXT              nullable
  created_at         DATETIME          NOT NULL
  updated_at         DATETIME          NOT NULL

Đây là thông tin khách hàng phục vụ đơn hàng; không xây dựng module quản
lý khách hàng độc lập trong MVP.

## 6.8. Bảng `sales_order_items`

  Cột          Kiểu              Quy tắc
  ------------ ----------------- --------------------
  id           BIGINT UNSIGNED   PK
  order_id     BIGINT UNSIGNED   FK sales_orders.id
  product_id   BIGINT UNSIGNED   FK products.id
  quantity     INT UNSIGNED      NOT NULL, \> 0
  unit_price   DECIMAL(14,2)     NOT NULL, \>= 0
  line_total   DECIMAL(14,2)     NOT NULL
  created_at   DATETIME          NOT NULL

Giá bán tại thời điểm tạo đơn phải được snapshot trong `unit_price`;
thay đổi giá sản phẩm về sau không làm thay đổi đơn cũ.

## 6.9. Bảng `stock_movements` (lịch sử kho)

  -----------------------------------------------------------------------
  Cột                     Kiểu                    Quy tắc
  ----------------------- ----------------------- -----------------------
  id                      BIGINT UNSIGNED         PK

  product_id              BIGINT UNSIGNED         FK products.id

  movement_type           VARCHAR(30)             purchase_in / sale_out
                                                  / sale_return /
                                                  adjustment

  quantity_delta          INT                     Có thể âm hoặc dương

  reference_type          VARCHAR(40)             purchase_receipt /
                                                  sales_order /
                                                  adjustment

  reference_id            BIGINT UNSIGNED         ID giao dịch tham chiếu
                          nullable                

  reason                  VARCHAR(255) nullable   Lý do điều chỉnh

  created_by              BIGINT UNSIGNED         FK users.id

  created_at              DATETIME                NOT NULL
  -----------------------------------------------------------------------

`stock_movements` là nhật ký bổ sung (append-only) trong nghiệp vụ
thường ngày. Không cho người dùng sửa/xóa lịch sử trực tiếp. Mọi lần
tăng/giảm kho phải tạo movement tương ứng.

## 6.10. Bảng `audit_logs`

  Cột           Kiểu                       Quy tắc
  ------------- -------------------------- --------------
  id            BIGINT UNSIGNED            PK
  user_id       BIGINT UNSIGNED nullable   FK users.id
  action        VARCHAR(80)                NOT NULL
  entity_type   VARCHAR(80)                NOT NULL
  entity_id     BIGINT UNSIGNED nullable   ID đối tượng
  description   VARCHAR(500)               nullable
  ip_address    VARCHAR(45) nullable       IPv4/IPv6
  created_at    DATETIME                   NOT NULL

Không ghi password, cookie, session token, secret hoặc dữ liệu nhạy cảm
vào audit log.

## 6.11. Quan hệ dữ liệu

``` text
businesses 1 ---- N products
categories 1 ---- N products
businesses 1 ---- N purchase_receipts
purchase_receipts 1 ---- N purchase_receipt_items
products 1 ---- N purchase_receipt_items
sales_orders 1 ---- N sales_order_items
products 1 ---- N sales_order_items
products 1 ---- N stock_movements
users 1 ---- N purchase_receipts
users 1 ---- N sales_orders
users 1 ---- N audit_logs
```

Sử dụng FK và quy tắc xóa phù hợp. Với dữ liệu đã được giao dịch tham
chiếu, ưu tiên `RESTRICT` hoặc soft delete để bảo toàn lịch sử.

------------------------------------------------------------------------

# 7. Quy tắc nghiệp vụ quan trọng

## 7.1. Nhập kho

1.  Người dùng chọn nhà cung cấp và thêm một hoặc nhiều sản phẩm.
2.  Backend kiểm tra nhà cung cấp đang hoạt động, sản phẩm hợp lệ, số
    lượng \> 0 và đơn giá không âm.
3.  Backend tự tính thành tiền từng dòng và tổng phiếu.
4.  Khi phiếu được xác nhận `completed`, dùng transaction:
    -   khóa các hàng sản phẩm phù hợp khi cần
        (`SELECT ... FOR UPDATE`);
    -   tăng `products.stock_quantity`;
    -   thêm `stock_movements` loại `purchase_in`;
    -   cập nhật trạng thái phiếu;
    -   ghi audit log.
5.  Nếu bất kỳ bước nào lỗi, rollback toàn bộ transaction.
6.  Không cho xác nhận cùng một phiếu hai lần.

MVP có thể cho tạo phiếu ở trạng thái draft; chỉ khi xác nhận mới cộng
tồn kho. Hủy phiếu đã hoàn thành cần nghiệp vụ đảo kho có audit log,
không xóa lịch sử.

## 7.2. Bán hàng

1.  Người dùng chọn sản phẩm, số lượng và nhập thông tin khách hàng tối
    thiểu.
2.  Backend lấy giá bán từ database; không tin giá gửi từ frontend nếu
    người dùng không có quyền đặc biệt.
3.  Kiểm tra số lượng tồn kho đủ đáp ứng.
4.  Khi xác nhận đơn `completed`, transaction phải:
    -   khóa hàng sản phẩm cần xuất;
    -   kiểm tra tồn kho hiện tại;
    -   giảm `stock_quantity`;
    -   thêm `stock_movements` loại `sale_out`;
    -   lưu đơn và các dòng đơn;
    -   cập nhật tổng tiền;
    -   ghi audit log.
5.  Nếu tồn kho không đủ hoặc lỗi DB, rollback toàn bộ.
6.  Chống double-submit bằng cách kiểm tra trạng thái đơn và sử dụng
    POST/redirect/GET; không xử lý hoàn thành hai lần.
7.  Không cho xóa cứng đơn hàng đã hoàn thành.

## 7.3. Hủy giao dịch

-   Chỉ cho hủy giao dịch theo các trạng thái được phép.
-   Hủy phiếu nhập đã hoàn thành phải giảm lại tồn kho theo lượng nhập;
    không cho tồn kho âm.
-   Hủy đơn bán đã hoàn thành phải hoàn kho theo lượng xuất, ghi
    movement `sale_return` hoặc loại movement đảo tương đương.
-   Mọi thao tác hủy cần ghi audit log.
-   Quy tắc chuyển trạng thái phải nằm trong service layer, không lặp
    lại ở nhiều route.

## 7.4. Tạo mã

-   SKU: nhập bởi admin hoặc sinh theo định dạng dễ đọc.
-   Mã phiếu nhập: ví dụ `PN-YYYYMMDD-XXXX`.
-   Mã đơn bán: ví dụ `SO-YYYYMMDD-XXXX`.
-   Đảm bảo unique bằng database constraint; không chỉ dựa vào kiểm tra
    ở Python.
-   Nếu trùng mã do request đồng thời, retry sinh mã hoặc trả lỗi an
    toàn.

------------------------------------------------------------------------

# 8. Chi tiết các module và CRUD

## 8.1. Đăng nhập và tài khoản

-   Login bằng username/email và password.
-   Logout bằng POST.
-   Hash mật khẩu an toàn.
-   Tài khoản inactive không thể đăng nhập.
-   Giới hạn tốc độ đăng nhập hoặc ít nhất có cơ chế giảm brute force ở
    tầng ứng dụng/proxy.
-   Session cookie production bật `HttpOnly`, `Secure` khi dùng HTTPS và
    `SameSite=Lax`.
-   Có CSRF protection cho các form thay đổi dữ liệu.
-   Admin tạo/sửa/kích hoạt/vô hiệu hóa user.
-   Không bắt buộc đăng ký công khai.
-   Tạo tài khoản admin đầu tiên bằng CLI/seed có kiểm soát, không
    hardcode mật khẩu mặc định production.

## 8.2. Quản lý sản phẩm

-   Danh sách có tìm kiếm theo SKU/tên, lọc danh mục/nhà cung cấp/trạng
    thái.
-   Phân trang phía server.
-   Tạo sản phẩm.
-   Xem chi tiết.
-   Sửa thông tin.
-   Kích hoạt/vô hiệu hóa sản phẩm.
-   Không sửa tồn kho trực tiếp bằng CRUD thông thường.
-   Cảnh báo tồn kho thấp nếu `stock_quantity <= reorder_level`.
-   Validate URL ảnh nếu dùng `image_url`; không tải URL về server để
    tránh SSRF.
-   Nếu không có ảnh, dùng ảnh placeholder nội bộ.

## 8.3. Quản lý danh mục

-   CRUD danh mục.
-   Không xóa danh mục còn sản phẩm tham chiếu; thông báo cho người
    dùng.
-   Có thể vô hiệu hóa danh mục thay vì xóa.
-   Tên danh mục cần quy tắc chống trùng phù hợp.

## 8.4. Quản lý nhà cung cấp

-   CRUD nhà cung cấp.
-   Tìm kiếm theo mã, tên, email, số điện thoại.
-   Validate email/phone ở mức hợp lý.
-   Không xóa cứng nhà cung cấp đã được dùng trong phiếu nhập hoặc sản
    phẩm; chuyển inactive.
-   Hiển thị số lượng sản phẩm liên kết và lịch sử nhập kho nếu có.

## 8.5. Quản lý phiếu nhập

-   Danh sách, lọc theo nhà cung cấp/ngày/trạng thái.
-   Tạo phiếu draft.
-   Thêm nhiều dòng sản phẩm.
-   Xem chi tiết.
-   Xác nhận nhập kho.
-   Hủy theo quy tắc nghiệp vụ.
-   Hiển thị tổng số lượng và tổng tiền.
-   Không cho sửa dòng phiếu đã completed; nếu cần điều chỉnh, tạo giao
    dịch điều chỉnh riêng.

## 8.6. Quản lý đơn bán hàng

-   Danh sách, lọc theo mã/ngày/trạng thái.
-   Tạo đơn draft.
-   Thêm sản phẩm, số lượng.
-   Hiển thị tồn kho và giá bán.
-   Xác nhận bán và trừ kho trong transaction.
-   Xem chi tiết đơn.
-   Hủy đơn theo quy tắc đảo kho.
-   Không xóa cứng đơn completed.

## 8.7. Dashboard

Hiển thị các KPI: - Tổng số sản phẩm đang hoạt động. - Tổng số nhà cung
cấp đang hoạt động. - Số sản phẩm dưới ngưỡng tồn kho. - Tổng giá trị
tồn kho ước tính (`stock_quantity * purchase_price`). - Số đơn bán trong
ngày/tháng. - Tổng giá trị đơn bán đã completed trong khoảng thời gian
được chọn. - Biểu đồ doanh thu theo ngày hoặc tháng (chỉ dựa trên đơn
completed). - Top sản phẩm bán chạy (nếu có đủ dữ liệu). - Giao dịch gần
đây.

Mỗi KPI phải có định nghĩa rõ ràng; không gọi "lợi nhuận" nếu chưa tính
giá vốn, trả hàng và chi phí đầy đủ. Dashboard phải truy vấn hiệu quả và
không tải toàn bộ lịch sử vào memory.

## 8.8. Audit log

Ghi lại các sự kiện quan trọng: đăng nhập thành công/thất bại ở mức phù
hợp, tạo/sửa/vô hiệu hóa sản phẩm, tạo nhà cung cấp, xác nhận nhập, xác
nhận bán, hủy giao dịch và quản lý user.

Không ghi thông tin bí mật hoặc nội dung nhạy cảm. Chỉ admin được xem
audit log.

------------------------------------------------------------------------

# 9. REST/API và cấu trúc backend

Ứng dụng có thể render trang bằng Jinja2 và dùng các route POST/GET
truyền thống. Với một số thao tác frontend, có thể bổ sung JSON API.
Tránh xây REST API riêng hoàn toàn nếu không cần thiết cho MVP.

## 9.1. Route trang gợi ý

``` text
GET  /login
POST /login
POST /logout
GET  /dashboard

GET  /products
GET  /products/new
POST /products/new
GET  /products/<id>
GET  /products/<id>/edit
POST /products/<id>/edit
POST /products/<id>/deactivate

GET  /categories
GET  /categories/new
POST /categories/new
GET  /categories/<id>/edit
POST /categories/<id>/edit
POST /categories/<id>/deactivate

GET  /businesses
GET  /businesses/new
POST /businesses/new
GET  /businesses/<id>
GET  /businesses/<id>/edit
POST /businesses/<id>/edit
POST /businesses/<id>/deactivate

GET  /purchases
GET  /purchases/new
POST /purchases/new
GET  /purchases/<id>
POST /purchases/<id>/complete
POST /purchases/<id>/cancel

GET  /sales
GET  /sales/new
POST /sales/new
GET  /sales/<id>
POST /sales/<id>/complete
POST /sales/<id>/cancel

GET  /users                  # admin only
POST /users/new              # admin only
POST /users/<id>/update      # admin only
POST /users/<id>/deactivate  # admin only

GET  /audit-logs             # admin only
GET  /health                 # health check
```

Dùng ID số hoặc UUID theo một quy tắc thống nhất. Tất cả route thay đổi
dữ liệu dùng POST (hoặc method phù hợp), CSRF protection và permission
checks.

## 9.2. JSON API tùy chọn

Nếu cần API để demo hoặc kiểm thử: - `GET /api/health` -
`GET /api/products` - `GET /api/products/<id>` - `POST /api/products` -
`PATCH /api/products/<id>` - `DELETE /api/products/<id>` chỉ cho bản ghi
chưa được tham chiếu; mặc định nên dùng deactivate. - Tương tự cho
categories và businesses.

Chuẩn lỗi JSON:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dữ liệu chưa hợp lệ.",
    "details": {
      "name": "Tên sản phẩm là bắt buộc."
    }
  }
}
```

Không trả SQL, stack trace hoặc secret trong lỗi.

## 9.3. Phân lớp code

-   **Routes/Blueprints:** nhận request, xác thực quyền, trả response.
-   **Forms/Schemas:** validation đầu vào.
-   **Services:** nghiệp vụ, transaction, nhập/xuất kho.
-   **Models:** ORM và quan hệ.
-   **Repositories:** chỉ thêm nếu có nhu cầu thực sự; tránh
    overengineering.
-   **Templates:** HTML Jinja2.
-   **Utilities:** định dạng tiền/ngày, mã giao dịch.
-   **Config:** cấu hình theo environment.
-   **Extensions:** khởi tạo SQLAlchemy, Migrate, LoginManager, CSRF.
-   **CLI commands:** tạo admin, seed dữ liệu, kiểm tra hệ thống.

Nghiệp vụ nhập/xuất kho phải ở service layer để đảm bảo transaction và
test được.

------------------------------------------------------------------------

# 10. Cấu trúc thư mục đề xuất

``` text
tech-business-manager/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── business.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── purchase.py
│   │   ├── sale.py
│   │   ├── stock_movement.py
│   │   └── audit_log.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── products/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── categories/
│   ├── businesses/
│   ├── purchases/
│   ├── sales/
│   ├── users/
│   ├── audit/
│   ├── services/
│   │   ├── inventory_service.py
│   │   ├── purchase_service.py
│   │   ├── sales_service.py
│   │   └── audit_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── products/
│   │   ├── categories/
│   │   ├── businesses/
│   │   ├── purchases/
│   │   ├── sales/
│   │   ├── users/
│   │   └── errors/
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
├── migrations/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_products.py
│   ├── test_businesses.py
│   ├── test_purchases.py
│   ├── test_sales.py
│   └── test_inventory.py
├── scripts/
│   ├── create_admin.py
│   └── seed_demo.py
├── nginx/
│   └── default.conf
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── AWS_DEPLOYMENT.md
│   ├── SECURITY.md
│   └── DECISIONS.md
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── wsgi.py
├── Makefile
└── README.md
```

Có thể điều chỉnh cấu trúc nếu có lý do tốt, nhưng cần giữ rõ ranh giới
giữa route, service, model, template và cấu hình.

------------------------------------------------------------------------

# 11. Cấu hình môi trường và secrets

## 11.1. `.env.example`

Tạo file `.env.example` với placeholder, không dùng credential thật:

``` dotenv
APP_ENV=development
SECRET_KEY=replace-with-a-long-random-secret
APP_HOST=127.0.0.1
APP_PORT=8000

MYSQL_DATABASE=tech_business_db
MYSQL_USER=app_user
MYSQL_PASSWORD=replace-with-a-strong-password
MYSQL_ROOT_PASSWORD=replace-with-a-different-strong-password
DATABASE_URL=mysql+pymysql://app_user:replace-with-a-strong-password@db:3306/tech_business_db?charset=utf8mb4

SESSION_COOKIE_SECURE=false
LOG_LEVEL=INFO
TZ=Asia/Ho_Chi_Minh
```

Lưu ý: - `DATABASE_URL` cần URL-encode ký tự đặc biệt trong
username/password. - File `.env` phải được ignore trong Git. -
Production dùng `SESSION_COOKIE_SECURE=true` khi website đã phục vụ qua
HTTPS. - Không dùng giá trị mẫu ở production. - Không commit secret vào
GitHub, Docker image hoặc log. - Khi deploy, đặt environment variables
an toàn trên EC2 hoặc dùng AWS Systems Manager Parameter Store/Secrets
Manager nếu phù hợp ngân sách và yêu cầu. - Nếu đổi password database,
cập nhật secret và restart dịch vụ theo quy trình an toàn.

## 11.2. Cấu hình app

-   `development`: debug có thể bật local; không expose ra public.
-   `testing`: database riêng, dữ liệu test.
-   `production`: debug tắt, secret bắt buộc, cookie bảo mật, logging
    chuẩn và cấu hình proxy đúng.
-   Không sử dụng `flask run` làm server production; chạy Gunicorn.
-   Chỉ tin `X-Forwarded-*` header khi request đến từ reverse proxy tin
    cậy và cấu hình proxy đúng.

------------------------------------------------------------------------

# 12. Docker và Docker Compose

## 12.1. Yêu cầu Dockerfile

-   Dùng base image Python slim đã pin version hợp lý.
-   Tạo non-root user chạy ứng dụng.
-   Cài dependencies theo `requirements.txt`.
-   Không COPY `.env`, private key, credential hoặc dữ liệu local nhạy
    cảm vào image.
-   Thêm `.dockerignore`.
-   Cấu hình Gunicorn cho production.
-   Không bật Flask debug.
-   Có health check nếu phù hợp.
-   Image nên nhỏ, không cài package hệ thống không cần thiết.
-   Có thể build lại image từ source một cách lặp lại được.

## 12.2. Docker Compose local

Các service: - `web`: Flask + Gunicorn (hoặc Flask dev server chỉ dùng
trong profile development). - `db`: MySQL 8. - `nginx`: reverse proxy
(nếu dùng trong local).

Yêu cầu: - `db` có named volume. - App phụ thuộc vào health check của
DB, không chỉ dựa vào thứ tự khởi động. - MySQL chỉ expose cổng local
nếu thực sự cần debug, ví dụ bind `127.0.0.1:3306:3306`; không bind
`0.0.0.0` mặc định. - Production không publish cổng MySQL. - Sử dụng
internal Docker network. - Có restart policy phù hợp. - Không đặt
password mặc định yếu trong Compose production. - Migrations được chạy
như bước deploy có kiểm soát, không chạy đồng thời tùy tiện từ mọi
worker. - Backup database phải có quy trình riêng; named volume không
thay thế backup.

Lệnh local mong muốn:

``` bash
cp .env.example .env
# Chỉnh .env bằng secret local
docker compose up --build -d
docker compose ps
docker compose logs -f web
docker compose exec web flask --app wsgi db upgrade
```

Tên lệnh migration có thể thay đổi theo cách khởi tạo Flask-Migrate. Tài
liệu README phải ghi đúng lệnh thực tế sau khi code hoàn thiện.

## 12.3. Tách cấu hình production

`docker-compose.prod.yml`: - Không bật debug. - Không map MySQL port ra
host. - Dùng restart policy. - Dùng volume bền vững. - Chỉ expose Nginx
port 80/443. - Cấu hình Gunicorn. - Đặt health check. - Không mount
source code từ host vào container production. - Secret được cấp từ
environment/secret store, không ghi trực tiếp vào file tracked. - Có
hướng dẫn nâng cấp image và rollback.

------------------------------------------------------------------------

# 13. Thiết kế AWS và chuẩn bị EC2

## 13.1. Kiến trúc AWS MVP

-   **Amazon EC2:** máy ảo Ubuntu LTS chạy Docker Compose.
-   **Amazon EBS:** ổ đĩa root và dữ liệu bền vững. Docker named volume
    nằm trên filesystem của EC2/EBS; xác minh vị trí mount thực tế.
-   **Security Group:** firewall ở cấp instance.
-   **AWS IAM:** tài khoản/role theo nguyên tắc least privilege.
-   **Amazon CloudWatch (tùy chọn):** metrics/logs; cần cài/cấu hình
    agent nếu muốn thu thập log hệ thống/container theo cách cụ thể.
-   **AWS Budgets / Billing alerts:** cảnh báo chi phí.
-   **Elastic IP (tùy chọn):** IP tĩnh; kiểm tra chi phí áp dụng hiện
    hành trước khi sử dụng.
-   **Route 53 (tùy chọn):** DNS nếu cần mua/quản lý domain bằng AWS. Có
    thể dùng DNS nhà cung cấp khác.

Không bắt buộc dùng S3, RDS, Load Balancer hoặc NAT Gateway trong MVP.
Các thành phần đó có thể phát sinh chi phí. Nếu dùng S3 cho backup, cần
thiết kế IAM và lifecycle policy riêng.

## 13.2. Security Group

Quy tắc gợi ý: - TCP 80: mở Internet nếu website phục vụ HTTP hoặc
redirect sang HTTPS. - TCP 443: mở Internet khi đã cấu hình HTTPS. - TCP
22 (SSH): chỉ cho phép IP công cộng của người quản trị, không mở
`0.0.0.0/0` nếu tránh được. - TCP 3306: không mở public. - Không mở cổng
Flask/Gunicorn như 5000/8000 ra Internet. - Nếu dùng AWS Systems Manager
Session Manager và đã cấu hình IAM/agent/network cần thiết, có thể hạn
chế hoặc bỏ SSH inbound.

Đây là cấu hình mẫu; chỉ mở cổng thực sự cần dùng.

## 13.3. Quy trình tạo EC2

1.  Chọn AWS Region gần người dùng hoặc phù hợp mục tiêu học tập và ngân
    sách.
2.  Chọn Ubuntu Server LTS, kiến trúc CPU phù hợp với Docker image.
3.  Chọn instance nhỏ đủ chạy ứng dụng và MySQL demo; không cố định loại
    instance trước khi kiểm tra giá/credit và yêu cầu RAM.
4.  Gắn EBS volume có dung lượng hợp lý.
5.  Cấu hình key pair hoặc Session Manager.
6.  Tạo Security Group theo nguyên tắc least privilege.
7.  Gắn IAM role tối thiểu cần thiết; không nhúng access key vào EC2.
8.  SSH/SSM vào máy, cập nhật hệ điều hành và cài Docker Engine +
    Compose plugin từ nguồn chính thức.
9.  Tạo thư mục deploy, clone repository hoặc tải release/image.
10. Tạo `.env` production bằng phương thức an toàn.
11. Build/pull image và khởi chạy Docker Compose.
12. Chạy migration có kiểm soát.
13. Tạo tài khoản admin bằng CLI an toàn.
14. Kiểm tra health endpoint và các chức năng CRUD.
15. Cấu hình HTTPS và domain nếu có.
16. Kiểm tra log, reboot thử trong thời gian bảo trì và xác minh
    database vẫn tồn tại.
17. Thiết lập backup, monitoring và billing alert.

## 13.4. HTTPS

Không thu thập mật khẩu qua HTTP không mã hóa. Với triển khai public,
cần HTTPS.

Các lựa chọn: - Dùng domain và Nginx + Let's Encrypt/certbot, có quy
trình gia hạn chứng chỉ. - Dùng Cloudflare làm DNS/proxy nếu domain được
cấu hình đúng, nhưng cần cấu hình chế độ SSL/TLS phù hợp; không coi
Cloudflare là lý do để bỏ HTTPS giữa Cloudflare và origin. - Với kiến
trúc production lớn hơn, cân nhắc Application Load Balancer + ACM; ALB
có chi phí riêng và không cần thiết cho MVP một EC2.

Nếu chưa có domain, có thể test tạm bằng IP và HTTP trong môi trường
không chứa dữ liệu thật; trước khi dùng thật phải cấu hình HTTPS.

## 13.5. Lưu trữ và backup MySQL

-   Dùng Docker named volume hoặc bind mount được xác định rõ trên EBS.
-   Không coi container filesystem là nơi lưu database lâu dài.
-   Thiết lập `mysqldump` backup định kỳ cho demo nếu cần.
-   Backup phải được lưu ngoài volume dữ liệu chính nếu muốn chống mất ổ
    đĩa/instance; có thể chuyển bản backup đã mã hóa sang S3.
-   Không commit file backup chứa dữ liệu thật.
-   Kiểm tra khả năng restore trên database thử nghiệm.
-   Ghi rõ retention, thời điểm backup, nơi lưu và cách khôi phục.
-   Snapshot EBS có thể hỗ trợ phục hồi volume, nhưng phải hiểu tính
    nhất quán của database; snapshot không thay thế quy trình
    backup/restore đã kiểm thử.
-   Không xóa volume hoặc instance nếu chưa xác nhận dữ liệu và backup.

------------------------------------------------------------------------

# 14. Quy trình deploy và cập nhật phiên bản

MVP có thể deploy thủ công có kiểm soát:

1.  Pull code/release mới.
2.  Kiểm tra thay đổi migration.
3.  Backup DB trước migration quan trọng.
4.  Build image.
5.  Chạy migration một lần.
6.  Restart/recreate app container.
7.  Kiểm tra `/health`, đăng nhập và các CRUD chính.
8.  Xem logs.
9.  Nếu lỗi, quay lại image trước nếu migration tương thích; nếu
    migration phá vỡ schema thì cần kế hoạch rollback/forward-fix riêng.

Không chạy migration tự động từ mỗi worker lúc startup. Không dùng
`docker compose down -v` trên production vì `-v` có thể xóa volume và
mất dữ liệu.

Có thể mở rộng sau bằng GitHub Actions + ECR/SSH/SSM, nhưng không cần
xây CI/CD phức tạp trước khi MVP hoạt động ổn định. Nếu sử dụng ECR, IAM
và CI/CD, không lưu AWS access key dài hạn trong repository.

------------------------------------------------------------------------

# 15. Bảo mật tối thiểu

1.  Hash password an toàn; không mã hóa reversible và không lưu
    plaintext.
2.  CSRF protection cho mọi form thay đổi dữ liệu.
3.  Kiểm tra quyền ở backend.
4.  Validate và normalize input.
5.  Dùng ORM/parameterized queries.
6.  Bật cookie `HttpOnly`, `Secure` khi HTTPS và `SameSite`.
7.  Không bật debug trên production.
8.  Không trả stack trace ra trình duyệt.
9.  Secrets không được commit.
10. MySQL không public.
11. SSH chỉ giới hạn IP hoặc dùng Session Manager.
12. Cập nhật OS và base image định kỳ.
13. Dùng IAM least privilege; tránh dùng root credentials.
14. Ghi audit log các hành động quan trọng.
15. Giới hạn upload file nếu bổ sung tính năng upload; kiểm tra loại
    file, kích thước và tên file.
16. Cấu hình security headers phù hợp ở Nginx.
17. Giới hạn request body và timeout ở reverse proxy.
18. Không lưu dữ liệu thẻ thanh toán hoặc dữ liệu nhạy cảm không cần
    thiết.
19. Bảo vệ endpoint health: không để lộ thông tin môi trường, biến
    secret hoặc chi tiết database.
20. Có quy trình backup/restore đã thử nghiệm.

------------------------------------------------------------------------

# 16. Logging, monitoring và health checks

## 16.1. Application logs

-   Dùng Python logging.
-   Log ra stdout/stderr để Docker thu thập.
-   Log thời điểm, mức độ, request ID nếu có, route và kết quả.
-   Không log password, session cookie, authorization header, database
    URL đầy đủ hoặc secrets.
-   Cấu hình log rotation nếu ghi file trên host.

## 16.2. Health endpoint

`GET /health` trả về tối thiểu trạng thái ứng dụng, ví dụ:

``` json
{
  "status": "ok"
}
```

Không trả database credentials hoặc thông tin nội bộ. Có thể tạo
endpoint nội bộ kiểm tra database riêng, nhưng không tiết lộ chi tiết ra
public.

## 16.3. Chỉ số cần theo dõi

-   EC2 CPU utilization.
-   Network in/out.
-   Disk utilization và dung lượng EBS.
-   Memory usage (cần agent/metric bổ sung nếu muốn thấy trên
    CloudWatch).
-   Container status/restart count.
-   HTTP status code và response time nếu đã cấu hình metrics.
-   Database connection errors.
-   Disk space và dung lượng backup.

Không tuyên bố có metric nào nếu chưa cấu hình nguồn thu thập.

------------------------------------------------------------------------

# 17. Kiểm thử

Dùng `pytest` và test client của Flask. Test nghiệp vụ cần dùng database
test riêng, không bao giờ chạy test phá dữ liệu production.

## 17.1. Unit/integration tests

-   Login thành công/thất bại.
-   User inactive không đăng nhập được.
-   Staff không truy cập trang admin.
-   CRUD sản phẩm hợp lệ.
-   SKU trùng bị từ chối.
-   Giá âm bị từ chối.
-   Xóa/vô hiệu hóa sản phẩm đang được giao dịch tham chiếu.
-   Tạo phiếu nhập tăng kho đúng một lần.
-   Xác nhận phiếu nhập lần thứ hai bị từ chối.
-   Bán hàng giảm kho đúng.
-   Bán quá tồn kho bị từ chối.
-   Lỗi giữa transaction dẫn tới rollback.
-   Hủy đơn completed hoàn kho đúng và chỉ một lần.
-   Tồn kho không âm trong trường hợp nhiều request cùng bán một sản
    phẩm.
-   CSRF protection hoạt động.
-   Pagination và filter không làm lộ dữ liệu ngoài quyền.
-   Audit log được tạo cho các hành động cần ghi.
-   Health endpoint không tiết lộ secrets.

## 17.2. Kiểm thử trên EC2

-   Truy cập trang login qua domain/IP.
-   Đăng nhập và thao tác CRUD.
-   Kiểm tra cổng 3306 không thể truy cập public.
-   Restart container và kiểm tra dữ liệu vẫn còn.
-   Reboot EC2 trong thời gian kiểm thử và kiểm tra restart policy.
-   Kiểm tra logs.
-   Khôi phục backup vào database thử nghiệm.
-   Kiểm tra HTTPS và chứng chỉ khi đã cấu hình.
-   Đo thời gian phản hồi ở một số mức tải.
-   Ghi lại loại instance, Region, thời điểm và cấu hình để kết quả có
    thể tái lập.

## 17.3. Kịch bản tải thử nghiệm

Có thể sử dụng Locust hoặc k6 để tạo các mức tải tăng dần, ví dụ 5, 10,
25, 50 virtual users tùy năng lực instance. Đây là kịch bản thử nghiệm,
không phải yêu cầu hệ thống phải chịu được tất cả mức tải đó.

Ghi nhận: - Throughput (request/second). - Median và p95 response
time. - Error rate. - CPU/RAM/disk/network. - Chi phí ước tính theo thời
gian thử nghiệm.

Không chạy load test lớn trên AWS khi chưa đặt budget và kiểm tra khả
năng chịu tải; tải thử nghiệm có thể gây phát sinh chi phí hoặc làm ứng
dụng không phản hồi.

------------------------------------------------------------------------

# 18. Dashboard và dữ liệu demo

Seed data nên có: - 1 admin được tạo qua CLI (không hardcode mật khẩu
production). - 2--3 tài khoản staff demo chỉ trong development. - 6 danh
mục thiết bị. - 5--10 nhà cung cấp giả lập. - 30--50 sản phẩm giả lập. -
Một số phiếu nhập và đơn bán mẫu để dashboard có dữ liệu.

Ví dụ danh mục: - Laptop - Linh kiện máy tính - Màn hình - Thiết bị
ngoại vi - Thiết bị mạng - Phụ kiện

Ví dụ sản phẩm giả lập: - Laptop văn phòng 14 inch - Laptop gaming 15
inch - RAM DDR4 16GB - SSD NVMe 1TB - Màn hình 24 inch - Bàn phím cơ -
Chuột không dây - Router Wi-Fi

Không dùng thương hiệu, giá hoặc thông tin nhà cung cấp demo như dữ liệu
thị trường đã xác minh. Đánh dấu rõ đây là dữ liệu mẫu.

------------------------------------------------------------------------

# 19. Tiêu chí nghiệm thu (Definition of Done)

Dự án được xem là đạt MVP khi tất cả mục bắt buộc dưới đây hoàn thành:

## Chức năng

-   [ ] Login/logout hoạt động.
-   [ ] Phân quyền admin/staff được kiểm tra ở backend.
-   [ ] CRUD sản phẩm.
-   [ ] CRUD danh mục.
-   [ ] CRUD nhà cung cấp.
-   [ ] Tạo và xác nhận phiếu nhập.
-   [ ] Tạo và xác nhận đơn bán.
-   [ ] Tồn kho cập nhật đúng và không âm.
-   [ ] Hủy giao dịch tuân thủ quy tắc đảo kho.
-   [ ] Dashboard hiển thị số liệu đúng.
-   [ ] Tìm kiếm, lọc và phân trang hoạt động.
-   [ ] Audit log ghi hành động quan trọng.

## Chất lượng

-   [ ] Migrations hoạt động từ database rỗng.
-   [ ] Có seed script cho demo.
-   [ ] Test nghiệp vụ chính chạy thành công.
-   [ ] Có validation và xử lý lỗi.
-   [ ] Không có secret trong Git.
-   [ ] Không dùng debug server trên production.
-   [ ] Không public MySQL.
-   [ ] Dữ liệu tồn tại sau khi restart container.
-   [ ] Backup và restore được kiểm thử.

## Docker/AWS

-   [ ] `docker compose up --build` chạy local theo README.
-   [ ] Có production compose config.
-   [ ] Website truy cập được trên EC2.
-   [ ] Security Group chỉ mở các cổng cần thiết.
-   [ ] Có hướng dẫn cấu hình HTTPS hoặc ghi rõ điều kiện còn thiếu.
-   [ ] Có hướng dẫn backup, logs và cập nhật phiên bản.
-   [ ] Có hướng dẫn theo dõi AWS billing/budget.
-   [ ] Có số liệu thực nghiệm tối thiểu trong báo cáo.

------------------------------------------------------------------------

# 20. Tài liệu phải bàn giao

1.  Source code đầy đủ.
2.  `README.md` hướng dẫn setup local.
3.  `.env.example` không chứa secret.
4.  `Dockerfile`.
5.  `docker-compose.yml`.
6.  `docker-compose.prod.yml`.
7.  Migration scripts.
8.  Seed script.
9.  Test suite.
10. Sơ đồ kiến trúc.
11. ERD database.
12. Hướng dẫn triển khai EC2 (`docs/AWS_DEPLOYMENT.md`).
13. Hướng dẫn bảo mật (`docs/SECURITY.md`).
14. Hướng dẫn backup/restore.
15. Hướng dẫn vận hành và troubleshooting.
16. Bảng kết quả kiểm thử hiệu năng.
17. Bảng chi phí AWS dự kiến và cách theo dõi chi phí.
18. Danh sách giới hạn hiện tại và hướng phát triển.

------------------------------------------------------------------------

# 21. Hướng dẫn AWS deployment cần ghi trong README

Tài liệu deploy phải hướng dẫn theo trình tự và có lệnh cụ thể:

1.  Tạo/kiểm tra tài khoản AWS, Region và ngân sách.
2.  Tạo EC2 Ubuntu LTS.
3.  Tạo Security Group đúng nguyên tắc.
4.  Kết nối qua SSH giới hạn IP hoặc Session Manager.
5.  Cài Docker Engine và Docker Compose plugin từ hướng dẫn chính thức.
6.  Clone repository.
7.  Tạo `.env` production từ secret mạnh.
8.  Build và start các container.
9.  Chạy migration.
10. Tạo admin bằng lệnh CLI.
11. Kiểm tra health endpoint và log.
12. Cấu hình domain và HTTPS.
13. Cấu hình backup/restore.
14. Cấu hình monitoring.
15. Kiểm tra AWS Billing và Budgets.
16. Hướng dẫn cập nhật phiên bản và rollback.
17. Hướng dẫn dừng/xóa tài nguyên an toàn khi kết thúc đồ án.

Không ghi một mức giá AWS cố định trong tài liệu nếu chưa tra bảng giá
hiện hành theo Region, loại instance, EBS, truyền dữ liệu và các dịch vụ
bổ sung. Ghi rõ các tài nguyên có thể tiếp tục phát sinh phí kể cả khi
ứng dụng không có người truy cập.

------------------------------------------------------------------------

# 22. Hướng dẫn trình tự code cho AI

Thực hiện theo thứ tự:

### Task 1 --- Bootstrap

-   Tạo Flask app factory.
-   Cấu hình environment.
-   Khởi tạo extensions.
-   Tạo health endpoint.
-   Tạo Dockerfile, Compose và DB connection.
-   Xác minh ứng dụng khởi động local.

### Task 2 --- Database

-   Tạo models và relationships.
-   Thêm migrations.
-   Viết seed script.
-   Tạo ERD trong docs.
-   Kiểm tra migration từ database trống.

### Task 3 --- Auth và layout

-   Login/logout.
-   Flask-Login.
-   Password hashing.
-   CSRF.
-   Role checks.
-   Base template, sidebar, topbar và responsive layout.

### Task 4 --- CRUD cơ bản

-   Categories.
-   Businesses.
-   Products.
-   Pagination, filter, validation và audit logs.

### Task 5 --- Nghiệp vụ kho

-   Purchase receipts.
-   Sales orders.
-   Stock movements.
-   Transaction và chống xử lý lặp.
-   Test đồng thời ở mức phù hợp.

### Task 6 --- Dashboard

-   KPI.
-   Biểu đồ nếu hữu ích.
-   Giao dịch gần đây.
-   Truy vấn có index và giới hạn.

### Task 7 --- Hardening

-   Error handlers.
-   Logging.
-   Security headers.
-   Session cookie.
-   Health checks.
-   Kiểm tra secret leakage.
-   Backup/restore documentation.

### Task 8 --- Production container

-   Gunicorn.
-   Nginx.
-   Compose production.
-   Persistent volume.
-   Không publish DB port.
-   Hướng dẫn cập nhật và rollback.

### Task 9 --- AWS

-   Viết hướng dẫn EC2 chi tiết.
-   Viết checklist Security Group/IAM.
-   Viết cấu hình HTTPS.
-   Viết hướng dẫn CloudWatch nếu triển khai.
-   Viết hướng dẫn AWS Budgets.
-   Không tự động tạo tài nguyên thật nếu chưa được yêu cầu xác nhận.

### Task 10 --- Nghiệm thu

-   Chạy toàn bộ test.
-   Kiểm thử CRUD.
-   Kiểm thử nhập/xuất kho.
-   Kiểm thử persistence sau restart.
-   Kiểm thử quyền truy cập.
-   Ghi lại kết quả, lỗi còn tồn tại và cách tái hiện.
-   Cập nhật README theo trạng thái thực tế; không ghi rằng chức năng đã
    hoàn thành nếu chưa kiểm thử.

------------------------------------------------------------------------

# 23. Yêu cầu cuối cùng

Hãy coi đây là một ứng dụng quản trị kinh doanh nhỏ nhưng có quy tắc tồn
kho đúng và có khả năng triển khai thật, không phải chỉ là giao diện
minh họa.

Ưu tiên theo thứ tự:

1.  **Đúng nghiệp vụ và dữ liệu.**
2.  **Bảo mật và phân quyền.**
3.  **Chạy local bằng Docker một cách lặp lại được.**
4.  **Triển khai được trên EC2 theo hướng dẫn.**
5.  **Có kiểm thử và tài liệu đầy đủ.**
6.  **Giao diện đẹp, responsive và dễ sử dụng.**
7.  **Bổ sung tính năng nâng cao chỉ sau khi MVP ổn định.**

Nếu phải đánh đổi, hãy giữ nghiệp vụ, bảo mật, dữ liệu bền vững và khả
năng deploy trước các hiệu ứng giao diện không thiết yếu.
