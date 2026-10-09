from flask import Blueprint, redirect, render_template, url_for

from app.auth.permissions import admin_required
from app.services.workspace_service import database_available

blueprint = Blueprint("admin", __name__)


@blueprint.get("/admin")
@admin_required
def index():
    return redirect(url_for("admin.dashboard"))


@blueprint.get("/admin/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html", active_page="dashboard",
                           database_ok=database_available())
