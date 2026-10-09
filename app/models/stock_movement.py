from sqlalchemy.dialects.mysql import BIGINT

from app.extensions import db
from app.models.base import Record, TABLE_OPTIONS, foreign_id


class StockMovement(Record, db.Model):
    __tablename__ = "stock_movements"
    __table_args__ = (
        db.CheckConstraint("movement_type IN ('purchase_in', 'sale_out', 'sale_return', 'adjustment')", name="valid_movement_type"),
        db.CheckConstraint("reference_type IN ('purchase_receipt', 'sales_order', 'adjustment')", name="valid_reference_type"),
        db.Index("ix_stock_movements_reference", "reference_type", "reference_id"),
        TABLE_OPTIONS,
    )
    product_id = foreign_id("products.id")
    movement_type = db.Column(db.String(30), nullable=False)
    quantity_delta = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(40), nullable=False)
    reference_id = db.Column(BIGINT(unsigned=True))
    reason = db.Column(db.String(255))
    created_by = foreign_id("users.id")
    product = db.relationship("Product", back_populates="stock_movements")
    creator = db.relationship("User", back_populates="stock_movements")
