"""Controlled account creation; caller owns the transaction."""
import re

from app.extensions import db
from app.models import AuditLog, User


def create_admin(username: str, full_name: str, password: str, email: str | None = None) -> User:
    username = username.strip().lower()
    full_name = full_name.strip()
    email = email.strip().lower() if email and email.strip() else None
    if not re.fullmatch(r"[a-z0-9_.-]{3,80}", username):
        raise ValueError("Username cần 3–80 ký tự: chữ Latin, số, dấu chấm, gạch dưới hoặc gạch ngang.")
    if not full_name or len(full_name) > 120:
        raise ValueError("Họ tên cần từ 1 đến 120 ký tự.")
    if email and (len(email) > 190 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
        raise ValueError("Email chưa hợp lệ.")
    user = User(username=username, full_name=full_name, email=email, role="admin", is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(AuditLog(user_id=user.id, action="create_admin", entity_type="user",
                            entity_id=user.id, description="Khởi tạo Admin bằng CLI có kiểm soát."))
    return user
