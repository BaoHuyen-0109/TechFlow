import secrets

import pytest

from app import create_app
from app.config import load_config


@pytest.mark.parametrize("secret", ["", "short", "replace-with-a-long-random-secret"])
def test_missing_or_placeholder_secret_rejected(configured_env, monkeypatch, secret):
    monkeypatch.setenv("SECRET_KEY", secret)
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app()


def test_credentials_are_encoded_safely(configured_env, monkeypatch):
    password = secrets.token_hex(8) + "@:/?#%"
    monkeypatch.setenv("MYSQL_PASSWORD", password)
    url = load_config()["SQLALCHEMY_DATABASE_URI"]
    assert url.password == password
    assert url.host == "127.0.0.1"
    assert url.query["charset"] == "utf8mb4"


def test_production_requires_secure_cookies(configured_env, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError, match="HTTPS"):
        load_config()
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    config = load_config()
    assert config["SESSION_COOKIE_SECURE"]
    assert config["SESSION_COOKIE_HTTPONLY"]
    assert config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert config["DEBUG"] is False


def test_unknown_environment_rejected(configured_env, monkeypatch):
    monkeypatch.setenv("APP_ENV", "unknown")
    with pytest.raises(ValueError, match="APP_ENV"):
        load_config()


def test_missing_db_password_rejected(configured_env, monkeypatch):
    monkeypatch.delenv("MYSQL_PASSWORD")
    with pytest.raises(ValueError, match="database"):
        load_config()


def test_mysql_driver_required(configured_env, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(ValueError, match="MySQL"):
        load_config()
