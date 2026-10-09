from app.extensions import db
from app.models.base import Record, TABLE_OPTIONS, Timestamps


class Business(Record, Timestamps, db.Model):
    __tablename__ = "businesses"
    __table_args__ = (TABLE_OPTIONS,)
    code = db.Column(db.String(30), nullable=False, unique=True)
    name = db.Column(db.String(180), nullable=False, index=True)
    tax_code = db.Column(db.String(30), unique=True)
    contact_person = db.Column(db.String(120))
    email = db.Column(db.String(190))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true(), index=True)
    products = db.relationship("Product", back_populates="business", passive_deletes="all")
    purchase_receipts = db.relationship("PurchaseReceipt", back_populates="business", passive_deletes="all")
