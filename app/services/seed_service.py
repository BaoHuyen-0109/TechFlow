"""Insert-only demo catalog. Never reset stock, prices, or existing records."""
from decimal import Decimal

from flask import current_app
from sqlalchemy import select

from app.extensions import db
from app.models import Business, Category, Product

CATEGORIES = (
    ("Laptop", ("Laptop văn phòng 14 inch", "Laptop học tập 15 inch", "Laptop gaming 15 inch", "Laptop đồ họa 16 inch", "Laptop mỏng nhẹ 13 inch", "Laptop doanh nghiệp 14 inch"), 12_000_000),
    ("Linh kiện máy tính", ("RAM DDR4 16GB", "RAM DDR5 32GB", "SSD NVMe 1TB", "SSD SATA 512GB", "Nguồn máy tính 650W", "Vỏ máy tính ATX"), 800_000),
    ("Màn hình", ("Màn hình IPS 24 inch", "Màn hình IPS 27 inch", "Màn hình 4K 32 inch", "Màn hình gaming 165Hz", "Màn hình di động 15 inch", "Màn hình văn phòng 22 inch"), 2_000_000),
    ("Thiết bị ngoại vi", ("Bàn phím cơ", "Chuột không dây", "Tai nghe USB", "Webcam Full HD", "Micro để bàn", "Loa máy tính"), 300_000),
    ("Thiết bị mạng", ("Router Wi-Fi 6", "Switch 8 cổng", "Bộ phát Wi-Fi mesh", "USB Wi-Fi", "Bộ mở rộng sóng", "Card mạng PCIe"), 400_000),
    ("Phụ kiện", ("Hub USB-C", "Cáp HDMI 2m", "Giá đỡ laptop", "Túi đựng laptop", "Bộ vệ sinh máy tính", "Đế tản nhiệt laptop"), 100_000),
)


def seed_demo() -> dict[str, int]:
    if current_app.config["APP_ENV"] not in {"development", "testing"}:
        raise ValueError("Chỉ cho phép seed demo trong development/testing.")
    created = {"categories": 0, "businesses": 0, "products": 0}
    # One transaction also prevents partial seed on validation/unique conflicts.
    with db.session.begin():
        for number, (name, names, base_price) in enumerate(CATEGORIES, start=1):
            code = f"DEMO-CAT-{number:02d}"
            category = db.session.scalar(select(Category).where(Category.code == code))
            if category is None:
                category = Category(code=code, name=name, description="Danh mục mẫu phục vụ demo TechFlow.")
                db.session.add(category)
                db.session.flush()
                created["categories"] += 1
            supplier_code = f"DEMO-NCC-{number:02d}"
            business = db.session.scalar(select(Business).where(Business.code == supplier_code))
            if business is None:
                business = Business(code=supplier_code, name=f"Nhà cung cấp mẫu TechFlow {number:02d}",
                                    email=f"supplier{number}@example.invalid",
                                    address="Địa chỉ giả lập dùng cho đồ án",
                                    notes="DỮ LIỆU DEMO — không phải doanh nghiệp có thật.")
                db.session.add(business)
                db.session.flush()
                created["businesses"] += 1
            for variant, product_name in enumerate(names, start=1):
                sku = f"DEMO-SP-{number:02d}-{variant:02d}"
                if db.session.scalar(select(Product.id).where(Product.sku == sku)) is not None:
                    continue
                purchase_price = Decimal(base_price + (variant - 1) * (base_price // 10))
                db.session.add(Product(
                    sku=sku, name=product_name, category_id=category.id, business_id=business.id,
                    brand="TechFlow Demo", model=f"DEMO-{number:02d}{variant:02d}",
                    description="DỮ LIỆU DEMO — thông số và giá giả lập, không phải dữ liệu thị trường đã xác minh.",
                    purchase_price=purchase_price, selling_price=purchase_price * Decimal("1.20"),
                    stock_quantity=0, reorder_level=5,
                ))
                created["products"] += 1
    return created
