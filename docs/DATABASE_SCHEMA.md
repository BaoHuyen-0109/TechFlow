# Chi tiết schema MySQL

Xuất từ models bằng `python scripts/export_database_schema.py`.
Mô tả 15 bảng nghiệp vụ; không kết nối DB hoặc đọc secrets.
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
| warranty_enabled | BOOL | Không | DEFAULT false |
| warranty_months | INTEGER UNSIGNED | Có |  |
| warranty_notes | VARCHAR(2000) | Có |  |
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
- `ck_products_warranty_policy`: CHECK ((warranty_enabled = 0 AND warranty_months IS NULL) OR (warranty_enabled = 1 AND warranty_months IS NOT NULL AND warranty_months BETWEEN 1 AND 120))
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
| completed_at | DATETIME | Có |  |
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

## warranty_coverages

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| sale_item_id | BIGINT UNSIGNED | Không | FK sales_order_items.id, DELETE RESTRICT |
| enabled | BOOL | Không |  |
| months | INTEGER UNSIGNED | Có |  |
| notes | VARCHAR(2000) | Có |  |
| starts_on | DATE | Có |  |
| expires_on | DATE | Có |  |
| source | VARCHAR(20) | Không |  |
| verified_by | BIGINT UNSIGNED | Có | FK users.id, DELETE RESTRICT |
| verification_reason | VARCHAR(1000) | Có |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |

Indexes:

- `ix_warranty_coverages_expires_on`: expires_on
- `ix_warranty_coverages_sale_item_id`: sale_item_id
- `ix_warranty_coverages_verified_by`: verified_by

Constraints bổ sung:

- `ck_warranty_coverages_dates`: CHECK ((starts_on IS NULL AND expires_on IS NULL) OR (starts_on IS NOT NULL AND expires_on IS NOT NULL AND expires_on >= starts_on))
- `ck_warranty_coverages_policy`: CHECK ((enabled = 0 AND months IS NULL) OR (enabled = 1 AND months IS NOT NULL AND months BETWEEN 1 AND 120))
- `ck_warranty_coverages_valid_source`: CHECK (source IN ('sale', 'legacy_verified'))
- `uq_warranty_coverages_sale_item_id`: UNIQUE (sale_item_id)

## warranty_devices

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| coverage_id | BIGINT UNSIGNED | Không | FK warranty_coverages.id, DELETE RESTRICT |
| unit_index | INTEGER UNSIGNED | Không |  |
| serial | VARCHAR(100) | Có | UNIQUE |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |

Indexes:

- `ix_warranty_devices_coverage_id`: coverage_id

Constraints bổ sung:

- `ck_warranty_devices_unit_positive`: CHECK (unit_index > 0)
- `uq_warranty_devices_coverage_id`: UNIQUE (coverage_id, unit_index)
- `uq_warranty_devices_serial`: UNIQUE (serial)

## warranty_tickets

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| ticket_code | VARCHAR(40) | Không | UNIQUE |
| device_id | BIGINT UNSIGNED | Không | FK warranty_devices.id, DELETE RESTRICT |
| open_device_key | BIGINT UNSIGNED | Có | GENERATED ALWAYS (CASE WHEN status <> 'returned' THEN device_id ELSE NULL END) STORED |
| customer_id | BIGINT UNSIGNED | Có | FK customers.id, DELETE RESTRICT |
| customer_name | VARCHAR(150) | Không |  |
| customer_phone | VARCHAR(30) | Có |  |
| product_name | VARCHAR(180) | Không |  |
| product_sku | VARCHAR(50) | Không |  |
| created_by | BIGINT UNSIGNED | Không | FK users.id, DELETE RESTRICT |
| assigned_to | BIGINT UNSIGNED | Có | FK users.id, DELETE RESTRICT |
| status | VARCHAR(20) | Không | DEFAULT received |
| assessment | VARCHAR(20) | Không | DEFAULT pending |
| issue | VARCHAR(2000) | Không |  |
| inspection_result | VARCHAR(2000) | Có |  |
| rejection_reason | VARCHAR(1000) | Có |  |
| received_on | DATE | Không |  |
| promised_on | DATE | Có |  |
| completed_at | DATETIME | Có |  |
| returned_at | DATETIME | Có |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP, ORM cập nhật UTC |

Indexes:

- `ix_warranty_tickets_assigned_to`: assigned_to
- `ix_warranty_tickets_created_by`: created_by
- `ix_warranty_tickets_customer_id`: customer_id
- `ix_warranty_tickets_device_id`: device_id
- `ix_warranty_tickets_received_on`: received_on
- `ix_warranty_tickets_scope`: created_by, assigned_to, status
- `ix_warranty_tickets_status`: status

Constraints bổ sung:

- `ck_warranty_tickets_assessment_required`: CHECK (status NOT IN ('completed','returned') OR assessment <> 'pending')
- `ck_warranty_tickets_promise_date`: CHECK (promised_on IS NULL OR promised_on >= received_on)
- `ck_warranty_tickets_rejection_reason_required`: CHECK (assessment <> 'rejected' OR rejection_reason IS NOT NULL)
- `ck_warranty_tickets_valid_assessment`: CHECK (assessment IN ('pending','accepted','rejected'))
- `ck_warranty_tickets_valid_status`: CHECK (status IN ('received','processing','completed','rejected','returned'))
- `uq_warranty_tickets_open_device_key`: UNIQUE (open_device_key)
- `uq_warranty_tickets_ticket_code`: UNIQUE (ticket_code)

## warranty_events

| Cột | Kiểu MySQL | Nullable | Quy tắc |
| --- | --- | --- | --- |
| ticket_id | BIGINT UNSIGNED | Không | FK warranty_tickets.id, DELETE RESTRICT |
| actor_id | BIGINT UNSIGNED | Không | FK users.id, DELETE RESTRICT |
| action | VARCHAR(30) | Không |  |
| from_status | VARCHAR(20) | Có |  |
| to_status | VARCHAR(20) | Không |  |
| note | VARCHAR(2000) | Có |  |
| id | BIGINT UNSIGNED | Không | PK, AUTO_INCREMENT |
| created_at | DATETIME | Không | DEFAULT CURRENT_TIMESTAMP |

Indexes:

- `ix_warranty_events_actor_id`: actor_id
- `ix_warranty_events_ticket_id`: ticket_id

Constraints bổ sung:
