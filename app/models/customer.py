from app.extensions import db
from app.models.base import Record, Timestamps, TABLE_OPTIONS, foreign_id


class Customer(Record, Timestamps, db.Model):
    __tablename__ = 'customers'
    __table_args__ = (TABLE_OPTIONS,)
    name = db.Column(db.String(150), nullable=False, index=True)
    phone = db.Column(db.String(16), nullable=False, unique=True)
    email = db.Column(db.String(190))
    address = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true(), index=True)
    created_by = foreign_id('users.id')
    orders = db.relationship('SalesOrder', back_populates='customer', passive_deletes='all')
