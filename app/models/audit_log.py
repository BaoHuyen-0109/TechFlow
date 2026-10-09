from sqlalchemy.dialects.mysql import BIGINT

from app.extensions import db
from app.models.base import Record, TABLE_OPTIONS, foreign_id


class AuditLog(Record, db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = (
        db.Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        TABLE_OPTIONS,
    )
    user_id = foreign_id("users.id", nullable=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(BIGINT(unsigned=True))
    description = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    user = db.relationship("User", back_populates="audit_logs")
