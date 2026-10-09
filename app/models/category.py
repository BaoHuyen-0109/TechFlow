from app.extensions import db
from app.models.base import Record, TABLE_OPTIONS, Timestamps


class Category(Record, Timestamps, db.Model):
    __tablename__ = "categories"
    __table_args__ = (TABLE_OPTIONS,)
    code = db.Column(db.String(30), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true(), index=True)
    products = db.relationship("Product", back_populates="category", passive_deletes="all")
