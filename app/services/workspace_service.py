"""Read-only checks for the administration workspace."""
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db


def database_available() -> bool:
    try:
        with db.engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1
    except SQLAlchemyError:
        return False
