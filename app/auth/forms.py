from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import InputRequired, Length


class LoginForm(FlaskForm):
    identity = StringField("Tên đăng nhập hoặc email", validators=[
        InputRequired(message="Vui lòng nhập tên đăng nhập hoặc email."),
        Length(max=190, message="Thông tin đăng nhập quá dài."),
    ])
    password = PasswordField("Mật khẩu", validators=[
        InputRequired(message="Vui lòng nhập mật khẩu."),
        Length(max=128, message="Mật khẩu không hợp lệ."),
    ])
    next = HiddenField()
    submit = SubmitField("Đăng nhập")
