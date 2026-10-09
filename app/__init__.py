import logging

from flask import Flask

from app.config import load_config
from app.extensions import csrf, db, login_manager, migrate


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(load_config())
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    db.init_app(app)
    from app import models  # noqa: F401 -- register ORM metadata for migrations

    migrate.init_app(app, db)
    # Enable the user context processor in stage 3 alongside the real user_loader.
    login_manager.init_app(app, add_context_processor=False)
    csrf.init_app(app)

    from app.main.routes import blueprint
    from app.cli import register_commands
    from app.errors import register_error_handlers

    app.register_blueprint(blueprint)
    register_commands(app)
    register_error_handlers(app)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return app
