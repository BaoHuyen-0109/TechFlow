from sqlalchemy.dialects.mysql import INTEGER

from app.extensions import db
from app.models.base import Record, TABLE_OPTIONS, Timestamps, foreign_id


class PurchaseReceipt(Record, Timestamps, db.Model):
    __tablename__ = "purchase_receipts"
    __table_args__ = (
        db.CheckConstraint("status IN ('draft', 'completed', 'cancelled')", name="valid_status"),
        db.CheckConstraint("total_amount >= 0", name="total_nonnegative"),
        TABLE_OPTIONS,
    )
    receipt_code = db.Column(db.String(40), nullable=False, unique=True)
    business_id = foreign_id("businesses.id")
    created_by = foreign_id("users.id")
    receipt_date = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="draft", server_default="draft", index=True)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0, server_default="0")
    notes = db.Column(db.Text)
    business = db.relationship("Business", back_populates="purchase_receipts")
    creator = db.relationship("User", back_populates="purchase_receipts")
    items = db.relationship("PurchaseReceiptItem", back_populates="receipt", passive_deletes="all")


class PurchaseReceiptItem(Record, db.Model):
    __tablename__ = "purchase_receipt_items"
    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="quantity_positive"),
        db.CheckConstraint("unit_cost >= 0", name="unit_cost_nonnegative"),
        db.CheckConstraint("line_total = quantity * unit_cost", name="correct_line_total"),
        TABLE_OPTIONS,
    )
    receipt_id = foreign_id("purchase_receipts.id")
    product_id = foreign_id("products.id")
    quantity = db.Column(INTEGER(unsigned=True), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 2), nullable=False)
    line_total = db.Column(db.Numeric(14, 2), nullable=False)
    receipt = db.relationship("PurchaseReceipt", back_populates="items")
    product = db.relationship("Product", back_populates="purchase_items")
