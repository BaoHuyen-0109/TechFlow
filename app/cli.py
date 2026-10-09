import os

import click
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.services.health_service import check_database
from app.extensions import db
from app.services.account_service import create_admin
from app.services.seed_service import seed_demo


def register_commands(app: Flask) -> None:
    @app.cli.command("check-db")
    def check_db_command():
        """Check database connectivity without printing connection details."""
        try:
            check_database()
        except SQLAlchemyError:
            app.logger.error("Database connectivity check failed")
            raise click.ClickException("Không thể kết nối database. Kiểm tra cấu hình và service db.") from None
        click.echo("Kết nối database thành công.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Username")
    @click.option("--full-name", prompt="Họ tên")
    @click.option("--email", default=None, help="Email tùy chọn.")
    def create_admin_command(username: str, full_name: str, email: str | None):
        """Create an Admin; password comes from a hidden prompt or environment."""
        password = os.environ.get("TECHFLOW_ADMIN_PASSWORD")
        if password is None:
            password = click.prompt("Mật khẩu", hide_input=True, confirmation_prompt=True)
        try:
            with db.session.begin():
                create_admin(username, full_name, password, email)
        except ValueError as error:
            raise click.ClickException(str(error)) from None
        except SQLAlchemyError:
            raise click.ClickException("Không thể tạo Admin. Kiểm tra kết nối, migration và username/email trùng.") from None
        click.echo("Đã tạo Admin an toàn. Mật khẩu không được hiển thị hoặc ghi log.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Insert a repeatable demo catalog without overwriting existing rows."""
        try:
            created = seed_demo()
        except ValueError as error:
            raise click.ClickException(str(error)) from None
        except SQLAlchemyError:
            raise click.ClickException("Không thể seed. Kiểm tra migration, kết nối và dữ liệu trùng; transaction đã rollback.") from None
        click.echo("Dữ liệu demo đã được nạp. Bản ghi tạo mới: " + ", ".join(f"{key}={value}" for key, value in created.items()))
