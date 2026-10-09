from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from datetime import datetime
from zoneinfo import ZoneInfo

from app.auth.permissions import business_required

blueprint = Blueprint("dashboard", __name__)


@blueprint.get("/dashboard")
@login_required
def index():
    endpoint = "admin.dashboard" if current_user.role == "admin" else "dashboard.staff"
    return redirect(url_for(endpoint))


@blueprint.get("/staff/dashboard")
@business_required
def staff():
    return render_template("staff/dashboard.html", active_page="dashboard",
                           workspace_home=url_for("dashboard.staff"),
                           today=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")))
