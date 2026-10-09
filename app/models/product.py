from sqlalchemy.dialects.mysql import INTEGER

from app.extensions import db
from app.models.base import Record, TABLE_OPTIONS, Timestamps, foreign_id


class Product(Record, Timestamps, db.Model):
    __tablename__ = "products"
    __table_args__ = (
        db.CheckConstraint("purchase_price >= 0", name="purchase_price_nonnegative"),
        db.CheckConstraint("selling_price >= 0", name="selling_price_nonnegative"),
        TABLE_OPTIONS,
    )
    sku = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(180), nullable=False, index=True)
    category_id = foreign_id("categories.id")
    business_id = foreign_id("businesses.id", nullable=True)
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    description = db.Column(db.Text)
    purchase_price = db.Column(db.Numeric(14, 2), nullable=False)
    selling_price = db.Column(db.Numeric(14, 2), nullable=False)
    stock_quantity = db.Column(INTEGER(unsigned=True), nullable=False, default=0, server_default="0")
    reorder_level = db.Column(INTEGER(unsigned=True), nullable=False, default=5, server_default="5")
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true(), index=True)
    category = db.relationship("Category", back_populates="products")
    business = db.relationship("Business", back_populates="products")
    purchase_items = db.relationship("PurchaseReceiptItem", back_populates="product", passive_deletes="all")
    sale_items = db.relationship("SalesOrderItem", back_populates="product", passive_deletes="all")
    stock_movements = db.relationship("StockMovement", back_populates="product", passive_deletes="all")
