from flask import Blueprint, jsonify, render_template

blueprint = Blueprint("main", __name__)


@blueprint.get("/")
def index():
    return render_template("main/index.html")


@blueprint.get("/health")
def health():
    # Liveness only. Database readiness is checked separately via CLI.
    return jsonify(status="ok")
