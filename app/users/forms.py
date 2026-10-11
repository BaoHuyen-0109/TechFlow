import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError


def normalized_username(form, field):
    field.data = field.data.strip().lower()
    if not re.fullmatch(r"[a-z0-9_.-]{3,80}", field.data):
        raise ValidationError("Username cần 3–80 ký tự: chữ Latin, số, dấu chấm, gạch dưới hoặc gạch ngang.")


class StaffCreateForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(max=80), normalized_username])
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(min=1, max=120)])
    email = StringField("Email", validators=[Optional(), Length(max=190), Email()])
    password = PasswordField("Mật khẩu khởi tạo", validators=[DataRequired(), Length(min=12, max=128)])
    confirm_password = PasswordField("Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password", message="Mật khẩu nhập lại chưa khớp.")])
    submit = SubmitField("Tạo tài khoản Staff")


class StaffStateForm(FlaskForm):
    submit = SubmitField("Cập nhật trạng thái")
