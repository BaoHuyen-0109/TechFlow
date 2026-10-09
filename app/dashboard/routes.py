from flask import Blueprint, render_template
from flask_login import login_required

blueprint = Blueprint("dashboard", __name__)


@blueprint.get("/dashboard")
@login_required
def index():
    return render_template("dashboard/index.html", active_page="dashboard")
