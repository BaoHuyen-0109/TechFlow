from flask import Flask, render_template
from flask_wtf.csrf import CSRFError

from app.extensions import db


def register_error_handlers(app: Flask) -> None:
    messages = {
        400: "Yêu cầu chưa hợp lệ. Vui lòng tải lại trang và thử lại.",
        403: "Bạn không có quyền truy cập trang này.",
        404: "Trang bạn tìm kiếm không tồn tại.",
        413: "Dữ liệu gửi lên vượt quá giới hạn cho phép.",
        500: "Hệ thống gặp sự cố. Vui lòng thử lại sau.",
    }

    def handle_error(error):
        code = getattr(error, "code", 500)
        if code == 500:
            db.session.rollback()
            # Avoid logging exception details which may contain a database URL.
            app.logger.error("Internal server error on request")
        return render_template("errors/error.html", code=code, message=messages[code]), code

    for code in messages:
        app.register_error_handler(code, handle_error)
    app.register_error_handler(CSRFError, handle_error)
