"""Environment configuration; values are read when the factory is called."""
import os
from pathlib import Path
from datetime import timedelta

from sqlalchemy.engine import URL, make_url


def load_config() -> dict:
    environment = os.getenv("APP_ENV", "development")
    if environment not in {"development", "testing", "production"}:
        raise ValueError("APP_ENV không hợp lệ.")
    secret = os.getenv("SECRET_KEY", "")
    if len(secret) < 32 or secret.startswith("replace-"):
        raise ValueError("SECRET_KEY phải có ít nhất 32 ký tự và không dùng giá trị mẫu.")
    raw_url = os.getenv("DATABASE_URL")
    if raw_url:
        database_url = make_url(raw_url)
    else:
        required = ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
        if any(not os.getenv(key) for key in required):
            raise ValueError("Thiếu cấu hình kết nối database.")
        database_url = URL.create(
            "mysql+pymysql",
            username=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            host=os.getenv("DB_HOST", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=os.environ["MYSQL_DATABASE"],
            query={"charset": "utf8mb4"},
        )
    if database_url.drivername != "mysql+pymysql":
        raise ValueError("Ứng dụng yêu cầu MySQL với driver PyMySQL.")
    secure = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    if environment == "production" and not secure:
        raise ValueError("Production yêu cầu SESSION_COOKIE_SECURE=true và HTTPS.")
    upload_storage = os.getenv("UPLOAD_STORAGE", "s3" if environment == "production" else "local").lower()
    if upload_storage not in {"local", "s3"}:
        raise ValueError("UPLOAD_STORAGE chỉ nhận local hoặc s3.")
    s3_bucket = os.getenv("S3_BUCKET", "").strip()
    aws_region = os.getenv("AWS_REGION", "ap-southeast-2").strip()
    if upload_storage == "s3" and s3_bucket and (not 3 <= len(s3_bucket) <= 63 or not s3_bucket.islower()):
        raise ValueError("S3_BUCKET chưa đúng định dạng tên bucket S3.")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("LOG_LEVEL không hợp lệ.")
    return {
        "APP_ENV": environment,
        "SECRET_KEY": secret,
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "hide_parameters": True,
            "pool_pre_ping": True,
            "pool_recycle": 280,
            "connect_args": {"connect_timeout": 5, "init_command": "SET time_zone = '+00:00'"},
        },
        "DEBUG": False,
        "TESTING": environment == "testing",
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": secure,
        "MAX_CONTENT_LENGTH": 8 * 1024 * 1024,
        "UPLOAD_STORAGE": upload_storage,
        "S3_BUCKET": s3_bucket,
        "AWS_REGION": aws_region,
        "PRODUCT_UPLOAD_DIR": str(Path(__file__).resolve().parent / "static" / "uploads" / "products"),
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=8),
        "LOGIN_MAX_FAILURES": 5,
        "LOGIN_WINDOW_MINUTES": 15,
        "LOG_LEVEL": log_level,
    }
