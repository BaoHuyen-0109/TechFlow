"""Immutable sale policy, sparse unit identities and append-only handling history."""
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from app.extensions import db
from app.models.base import Record, Timestamps, TABLE_OPTIONS, foreign_id


class WarrantyCoverage(Record, db.Model):
    __tablename__ = 'warranty_coverages'
    __table_args__ = (
        db.UniqueConstraint('sale_item_id'),
        db.CheckConstraint("source IN ('sale', 'legacy_verified')", name='valid_source'),
        db.CheckConstraint('(enabled = 0 AND months IS NULL) OR (enabled = 1 AND months IS NOT NULL AND months BETWEEN 1 AND 120)', name='policy'),
        db.CheckConstraint('(starts_on IS NULL AND expires_on IS NULL) OR (starts_on IS NOT NULL AND expires_on IS NOT NULL AND expires_on >= starts_on)', name='dates'),
        TABLE_OPTIONS,
    )
    sale_item_id = foreign_id('sales_order_items.id')
    enabled = db.Column(db.Boolean, nullable=False)
    months = db.Column(INTEGER(unsigned=True))
    notes = db.Column(db.String(2000))
    starts_on = db.Column(db.Date)
    expires_on = db.Column(db.Date, index=True)
    source = db.Column(db.String(20), nullable=False)
    verified_by = foreign_id('users.id', nullable=True)
    verification_reason = db.Column(db.String(1000))
    item = db.relationship('SalesOrderItem')


class WarrantyDevice(Record, db.Model):
    __tablename__ = 'warranty_devices'
    __table_args__ = (db.UniqueConstraint('coverage_id', 'unit_index'),
        db.CheckConstraint('unit_index > 0', name='unit_positive'), TABLE_OPTIONS)
    coverage_id = foreign_id('warranty_coverages.id')
    unit_index = db.Column(INTEGER(unsigned=True), nullable=False)
    serial = db.Column(db.String(100), unique=True)
    coverage = db.relationship('WarrantyCoverage')


class WarrantyTicket(Record, Timestamps, db.Model):
    __tablename__ = 'warranty_tickets'
    __table_args__ = (
        db.CheckConstraint("status IN ('received','processing','completed','rejected','returned')", name='valid_status'),
        db.CheckConstraint("assessment IN ('pending','accepted','rejected')", name='valid_assessment'),
        db.CheckConstraint("status NOT IN ('completed','returned') OR assessment <> 'pending'", name='assessment_required'),
        db.CheckConstraint("assessment <> 'rejected' OR rejection_reason IS NOT NULL", name='rejection_reason_required'),
        db.CheckConstraint('promised_on IS NULL OR promised_on >= received_on', name='promise_date'),
        db.UniqueConstraint('open_device_key'),
        db.Index('ix_warranty_tickets_scope', 'created_by', 'assigned_to', 'status'), TABLE_OPTIONS)
    ticket_code = db.Column(db.String(40), nullable=False, unique=True)
    device_id = foreign_id('warranty_devices.id')
    open_device_key = db.Column(BIGINT(unsigned=True), db.Computed("CASE WHEN status <> 'returned' THEN device_id ELSE NULL END", persisted=True))
    customer_id = foreign_id('customers.id', nullable=True)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(30))
    product_name = db.Column(db.String(180), nullable=False)
    product_sku = db.Column(db.String(50), nullable=False)
    created_by = foreign_id('users.id')
    assigned_to = foreign_id('users.id', nullable=True)
    status = db.Column(db.String(20), nullable=False, default='received', server_default='received', index=True)
    assessment = db.Column(db.String(20), nullable=False, default='pending', server_default='pending')
    issue = db.Column(db.String(2000), nullable=False)
    inspection_result = db.Column(db.String(2000))
    rejection_reason = db.Column(db.String(1000))
    received_on = db.Column(db.Date, nullable=False, index=True)
    promised_on = db.Column(db.Date)
    completed_at = db.Column(db.DateTime)
    returned_at = db.Column(db.DateTime)
    device = db.relationship('WarrantyDevice')
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    creator = db.relationship('User', foreign_keys=[created_by])


class WarrantyEvent(Record, db.Model):
    __tablename__ = 'warranty_events'
    __table_args__ = (TABLE_OPTIONS,)
    ticket_id = foreign_id('warranty_tickets.id')
    actor_id = foreign_id('users.id')
    action = db.Column(db.String(30), nullable=False)
    from_status = db.Column(db.String(20))
    to_status = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(2000))
    actor = db.relationship('User')
