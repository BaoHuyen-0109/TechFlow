"""Authentication with persistent throttling shared by all Gunicorn workers."""
from datetime import timedelta
import hashlib
import hmac
import secrets

from flask import current_app
from sqlalchemy import func, or_, select, text
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import AuditLog, User
from app.models.base import utc_now

# Equal-cost password verification for unknown accounts; never a login credential.
DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32), method="scrypt")


def authenticate(identity: str, password: str, ip_address: str | None) -> tuple[User | None, bool]:
    identity = identity.strip().lower()
    user = db.session.scalar(select(User).where(or_(User.username == identity, User.email == identity)))
    # Use the same bucket for username and email of an existing account.
    subject = f"user:{user.id}" if user else f"unknown:{identity}"
    bucket = hmac.new(current_app.secret_key.encode(), subject.encode(), hashlib.sha256).hexdigest()
    lock_name = bucket  # MySQL advisory lock name is at most 64 characters.
    cutoff = utc_now() - timedelta(minutes=current_app.config["LOGIN_WINDOW_MINUTES"])
    # A separate connection owns the advisory lock through commit of the attempt.
    # This serializes concurrent attempts for one account across processes.
    with db.engine.connect() as lock_connection:
        acquired = lock_connection.execute(text("SELECT GET_LOCK(:key, 3)"), {"key": lock_name}).scalar()
        if acquired != 1:
            db.session.rollback()
            return None, True
        try:
            # End the lookup transaction so the count sees other workers' commits.
            db.session.commit()
            failures = db.session.scalar(select(func.count()).select_from(AuditLog).where(
                AuditLog.action == "login_failed", AuditLog.entity_type == "auth_attempt",
                AuditLog.description == bucket, AuditLog.created_at >= cutoff,
            ))
            if failures >= current_app.config["LOGIN_MAX_FAILURES"]:
                db.session.rollback()
                return None, True
            # Refresh account state after acquiring the shared lock.
            if user is not None:
                db.session.refresh(user)
            verified = check_password_hash(user.password_hash if user else DUMMY_HASH, password)
            if user is None or not user.is_active or not verified or user.role not in {"admin", "staff"}:
                db.session.add(AuditLog(action="login_failed", entity_type="auth_attempt",
                                        description=bucket, ip_address=ip_address))
                db.session.commit()
                return None, False
            user.last_login_at = utc_now()
            db.session.add(AuditLog(user_id=user.id, action="login_success", entity_type="user",
                                    entity_id=user.id, ip_address=ip_address))
            db.session.commit()
            return user, False
        except Exception:
            db.session.rollback()
            raise
        finally:
            lock_connection.execute(text("SELECT RELEASE_LOCK(:key)"), {"key": lock_name})
