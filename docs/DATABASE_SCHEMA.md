# Chi tiết schema MySQL

Xuất từ models bằng `python scripts/export_database_schema.py`.
Mô tả 11 bảng nghiệp vụ; không kết nối DB hoặc đọc secrets.
Giai đoạn 5.1 bổ sung customers và liên kết tùy chọn vào đơn bán; xem [CUSTOMERS.md](CUSTOMERS.md).

## businesses

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| code | VARCHAR(30) | Không | UNIQUE |
| name | VARCHAR(180) | Không |  |
| tax_code | VARCHAR(30) | Có | UNIQUE |
| contact_person | VARCHAR(120) | Có |  |
| email | VARCHAR(190) | Có |  |
| phone | VARCHAR(30) | Có |  |
| address | VARCHAR(255) | Có |  |
| notes | TEXT | Có |  |
| is_active | BOOL | Không | DEFAULT true |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_businesses_is_active`: is_active
- `ix_businesses_name`: name

Constraints bổ sung:

- `uq_businesses_code`: UNIQUE (code)
- `uq_businesses_tax_code`: UNIQUE (tax_code)

## categories

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| code | VARCHAR(30) | Không | UNIQUE |
| name | VARCHAR(100) | Không | UNIQUE |
| description | TEXT | Có |  |
| is_active | BOOL | Không | DEFAULT true |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_categories_is_active`: is_active

Constraints bổ sung:

- `uq_categories_code`: UNIQUE (code)
- `uq_categories_name`: UNIQUE (name)

## users

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| full_name | VARCHAR(120) | Không |  |
| username | VARCHAR(80) | Không | UNIQUE |
| email | VARCHAR(190) | Có | UNIQUE |
| password_hash | VARCHAR(255) | Không |  |
| role | VARCHAR(20) | Không |  |
| is_active | BOOL | Không | DEFAULT true |
| last_login_at | DATETIME | Có |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_users_is_active`: is_active

Constraints bổ sung:

- `ck_users_valid_role`: CHECK (role IN ('admin', 'staff'))
- `uq_users_email`: UNIQUE (email)
- `uq_users_username`: UNIQUE (username)

## audit_logs

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| user_id | BIGINT UNSIGNED | Có | FK users.id, DELETE RESTRICT |
| action | VARCHAR(80) | Không |  |
| entity_type | VARCHAR(80) | Không |  |
| entity_id | BIGINT UNSIGNED | Có |  |
| description | VARCHAR(500) | Có |  |
| ip_address | VARCHAR(45) | Có |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |

Indexes:

- `ix_audit_logs_action`: action
- `ix_audit_logs_entity`: entity_type, entity_id
- `ix_audit_logs_user_id`: user_id

Constraints bổ sung:


## customers

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| name | VARCHAR(150) | Không |  |
| phone | VARCHAR(16) | Không | UNIQUE |
| email | VARCHAR(190) | Có |  |
| address | VARCHAR(255) | Có |  |
| is_active | BOOL | Không | DEFAULT true |
| created_by | BIGINT UNSIGNED | Không | FK users.id, DELETE RESTRICT |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_customers_created_by`: created_by
- `ix_customers_is_active`: is_active
- `ix_customers_name`: name

Constraints bổ sung:

- `uq_customers_phone`: UNIQUE (phone)

## products

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| sku | VARCHAR(50) | Không | UNIQUE |
| name | VARCHAR(180) | Không |  |
| category_id | BIGINT UNSIGNED | Không | FK categories.id, DELETE RESTRICT |
| business_id | BIGINT UNSIGNED | Có | FK businesses.id, DELETE RESTRICT |
| brand | VARCHAR(100) | Có |  |
| model | VARCHAR(100) | Có |  |
| description | TEXT | Có |  |
| purchase_price | NUMERIC(14, 2) | Không |  |
| selling_price | NUMERIC(14, 2) | Không |  |
| stock_quantity | INTEGER UNSIGNED | Không | DEFAULT 0 |
| reorder_level | INTEGER UNSIGNED | Không | DEFAULT 5 |
| image_url | VARCHAR(500) | Có |  |
| is_active | BOOL | Không | DEFAULT true |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_products_business_id`: business_id
- `ix_products_category_id`: category_id
- `ix_products_is_active`: is_active
- `ix_products_name`: name

Constraints bổ sung:

- `ck_products_purchase_price_nonnegative`: CHECK (purchase_price >= 0)
- `ck_products_selling_price_nonnegative`: CHECK (selling_price >= 0)
- `uq_products_sku`: UNIQUE (sku)

## purchase_receipts

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| receipt_code | VARCHAR(40) | Không | UNIQUE |
| business_id | BIGINT UNSIGNED | Không | FK businesses.id, DELETE RESTRICT |
| created_by | BIGINT UNSIGNED | Không | FK users.id, DELETE RESTRICT |
| receipt_date | DATETIME | Không |  |
| status | VARCHAR(20) | Không | DEFAULT draft |
| total_amount | NUMERIC(14, 2) | Không | DEFAULT 0 |
| notes | TEXT | Có |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_purchase_receipts_business_id`: business_id
- `ix_purchase_receipts_created_by`: created_by
- `ix_purchase_receipts_receipt_date`: receipt_date
- `ix_purchase_receipts_status`: status

Constraints bổ sung:

- `ck_purchase_receipts_total_nonnegative`: CHECK (total_amount >= 0)
- `ck_purchase_receipts_valid_status`: CHECK (status IN ('draft', 'completed', 'cancelled'))
- `uq_purchase_receipts_receipt_code`: UNIQUE (receipt_code)

## purchase_receipt_items

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| receipt_id | BIGINT UNSIGNED | Không | FK purchase_receipts.id, DELETE RESTRICT |
| product_id | BIGINT UNSIGNED | Không | FK products.id, DELETE RESTRICT |
| quantity | INTEGER UNSIGNED | Không |  |
| unit_cost | NUMERIC(14, 2) | Không |  |
| line_total | NUMERIC(14, 2) | Không |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |

Indexes:

- `ix_purchase_receipt_items_product_id`: product_id
- `ix_purchase_receipt_items_receipt_id`: receipt_id

Constraints bổ sung:

- `ck_purchase_receipt_items_correct_line_total`: CHECK (line_total = quantity * unit_cost)
- `ck_purchase_receipt_items_quantity_positive`: CHECK (quantity > 0)
- `ck_purchase_receipt_items_unit_cost_nonnegative`: CHECK (unit_cost >= 0)

## sales_orders

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| order_code | VARCHAR(40) | Không | UNIQUE |
| customer_name | VARCHAR(150) | Không |  |
| customer_phone | VARCHAR(30) | Có |  |
| customer_email | VARCHAR(190) | Có |  |
| customer_address | VARCHAR(255) | Có |  |
| customer_id | BIGINT UNSIGNED | Có | FK customers.id, DELETE RESTRICT |
| created_by | BIGINT UNSIGNED | Không | FK users.id, DELETE RESTRICT |
| order_date | DATETIME | Không |  |
| status | VARCHAR(20) | Không | DEFAULT draft |
| total_amount | NUMERIC(14, 2) | Không | DEFAULT 0 |
| notes | TEXT | Có |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_sales_orders_created_by`: created_by
- `ix_sales_orders_customer_id`: customer_id
- `ix_sales_orders_customer_status_date`: customer_id, status, order_date
- `ix_sales_orders_order_date`: order_date
- `ix_sales_orders_status`: status

Constraints bổ sung:

- `ck_sales_orders_total_nonnegative`: CHECK (total_amount >= 0)
- `ck_sales_orders_valid_status`: CHECK (status IN ('draft', 'completed', 'cancelled'))
- `uq_sales_orders_order_code`: UNIQUE (order_code)

## stock_movements

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| product_id | BIGINT UNSIGNED | Không | FK products.id, DELETE RESTRICT |
| movement_type | VARCHAR(30) | Không |  |
| quantity_delta | INTEGER | Không |  |
| reference_type | VARCHAR(40) | Không |  |
| reference_id | BIGINT UNSIGNED | Có |  |
| reason | VARCHAR(255) | Có |  |
| created_by | BIGINT UNSIGNED | Không | FK users.id, DELETE RESTRICT |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |

Indexes:

- `ix_stock_movements_created_by`: created_by
- `ix_stock_movements_product_id`: product_id
- `ix_stock_movements_reference`: reference_type, reference_id

Constraints bổ sung:

- `ck_stock_movements_valid_movement_type`: CHECK (movement_type IN ('purchase_in', 'sale_out', 'sale_return', 'adjustment'))
- `ck_stock_movements_valid_reference_type`: CHECK (reference_type IN ('purchase_receipt', 'sales_order', 'adjustment'))

## sales_order_items

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| order_id | BIGINT UNSIGNED | Không | FK sales_orders.id, DELETE RESTRICT |
| product_id | BIGINT UNSIGNED | Không | FK products.id, DELETE RESTRICT |
| quantity | INTEGER UNSIGNED | Không |  |
| unit_price | NUMERIC(14, 2) | Không |  |
| line_total | NUMERIC(14, 2) | Không |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |

Indexes:

- `ix_sales_order_items_order_id`: order_id
- `ix_sales_order_items_product_id`: product_id

Constraints bổ sung:

- `ck_sales_order_items_correct_line_total`: CHECK (line_total = quantity * unit_price)
- `ck_sales_order_items_quantity_positive`: CHECK (quantity > 0)
- `ck_sales_order_items_unit_price_nonnegative`: CHECK (unit_price >= 0)

