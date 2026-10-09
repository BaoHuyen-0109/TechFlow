from sqlalchemy import text

from app.extensions import db


def check_database() -> None:
    """Raise on failure; never return credentials or engine details."""
    with db.engine.connect() as connection:
        connection.execute(text("SELECT 1"))
