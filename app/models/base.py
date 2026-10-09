"""Shared MySQL types and UTC timestamps (stored without timezone offset)."""
from datetime import datetime, timezone

from sqlalchemy.dialects.mysql import BIGINT

from app.extensions import db

TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def foreign_id(target: str, *, nullable: bool = False):
    return db.Column(
        BIGINT(unsigned=True), db.ForeignKey(target, ondelete="RESTRICT"),
        nullable=nullable, index=True,
    )


class Record:
    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now,
                           server_default=db.text("CURRENT_TIMESTAMP"))


class Timestamps:
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now,
                           onupdate=utc_now, server_default=db.text("CURRENT_TIMESTAMP"))
