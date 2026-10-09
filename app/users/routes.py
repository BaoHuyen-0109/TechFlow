from flask import Blueprint, render_template

from app.auth.permissions import admin_required

blueprint = Blueprint("admin", __name__)


@blueprint.get("/admin")
@admin_required
def index():
    # A real, read-only role-specific page; no user CRUD controls in stage 3.
    return render_template("admin/index.html", active_page="admin")
