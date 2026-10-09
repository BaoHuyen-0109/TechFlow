from unittest.mock import patch

from app.services.health_service import check_database


def test_database_check_executes_query(app):
    with app.app_context(), patch("app.services.health_service.db.engine.connect") as connect:
        check_database()
    connection = connect.return_value.__enter__.return_value
    assert str(connection.execute.call_args.args[0]) == "SELECT 1"
    connect.return_value.__exit__.assert_called_once()
