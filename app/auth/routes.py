from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from app.auth.forms import LoginForm
from app.extensions import db
from app.models import AuditLog
from app.services.auth_service import authenticate

blueprint = Blueprint("auth", __name__)


@blueprint.get("/auth/rate-limit")
def rate_limit():
    abort(429)


def safe_destination(value: str | None, role: str | None = None) -> str:
    # Keep the strict allowlist. Login sends each role only to its own workspace.
    allowed = {"/dashboard", "/admin", "/admin/dashboard", "/staff/dashboard"}
    if role is None:
        return value if value in allowed else url_for("dashboard.index")
    default = url_for("admin.dashboard" if role == "admin" else "dashboard.staff")
    return default


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(safe_destination(None, current_user.role))
    form = LoginForm()
    destination = safe_destination(form.next.data if request.method == "POST" else request.args.get("next"))
    form.next.data = destination
    status = 200
    if form.validate_on_submit():
        try:
            user, limited = authenticate(form.identity.data, form.password.data, request.remote_addr)
        except SQLAlchemyError:
            current_app.logger.error("Authentication database unavailable")
            flash("Hiện chưa thể đăng nhập. Vui lòng thử lại sau.", "danger")
            status = 503
        else:
            if limited:
                flash("Bạn đã thử đăng nhập quá nhiều lần. Vui lòng thử lại sau 15 phút.", "warning")
                status = 429
            elif user is None:
                flash("Thông tin đăng nhập không đúng hoặc tài khoản không khả dụng.", "danger")
                status = 401
            else:
                session.clear()  # Discard pre-login state and rotate the CSRF/session payload.
                login_user(user, remember=False, fresh=True)
                session.permanent = True
                flash("Đăng nhập thành công. Chào mừng bạn trở lại TechFlow!", "success")
                return redirect(safe_destination(destination, user.role))
    response = current_app.make_response((render_template("auth/login.html", form=form), status))
    if status == 429:
        response.headers["Retry-After"] = "900"
    return response


@blueprint.post("/logout")
@login_required
def logout():
    try:
        db.session.add(AuditLog(user_id=current_user.id, action="logout", entity_type="user",
                                entity_id=current_user.id, ip_address=request.remote_addr))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Logout audit unavailable")
    logout_user()
    session.clear()
    flash("Bạn đã đăng xuất an toàn.", "success")
    return redirect(url_for("auth.login"))
