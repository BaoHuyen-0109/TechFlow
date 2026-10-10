from unittest.mock import patch

from flask import abort
from sqlalchemy.exc import OperationalError


def test_liveness_does_not_require_database(app, client):
    with app.app_context(), patch("app.services.health_service.db.engine.connect") as connect:
        response = client.get("/health")
        connect.assert_not_called()
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_public_page_and_stylesheet(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'lang="vi"' in response.text
    assert "TechFlow" in response.text
    assert 'href="/login"' in response.text
    assert "giữa kỳ" not in response.text.lower()
    assert client.get("/static/css/foundation.css").status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_not_found_is_friendly(client):
    response = client.get("/missing")
    assert response.status_code == 404
    assert "không tồn tại" in response.text
    assert "Traceback" not in response.text


def test_internal_error_is_safe(app):
    @app.get("/test-error")
    def fail():
        abort(500)
    response = app.test_client().get("/test-error")
    assert response.status_code == 500
    assert "Vui lòng thử lại sau" in response.text
    assert "Traceback" not in response.text


def test_csrf_is_enabled(app, client):
    @app.post("/test-write")
    def write():
        return "written"
    response = client.post("/test-write")
    assert response.status_code == 400
    assert "written" not in response.text


def test_database_cli_success(app):
    with patch("app.cli.check_database") as check:
        result = app.test_cli_runner().invoke(args=["check-db"])
    check.assert_called_once()
    assert result.exit_code == 0
    assert "thành công" in result.output


def test_database_cli_does_not_expose_exception(app, caplog):
    error = OperationalError("SELECT 1", {}, Exception("sensitive-connection-detail"))
    with patch("app.cli.check_database", side_effect=error):
        result = app.test_cli_runner().invoke(args=["check-db"])
    assert result.exit_code == 1
    assert "Không thể kết nối" in result.output
    assert "sensitive-connection-detail" not in result.output + caplog.text
