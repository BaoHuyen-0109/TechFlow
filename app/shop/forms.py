from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


class RegisterForm(FlaskForm):
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(max=120)])
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3, max=80),
        Regexp(r"^[a-zA-Z0-9_.-]+$", message="Chỉ dùng chữ Latin, số, dấu chấm, gạch dưới hoặc gạch ngang.")])
    email = StringField("Email", validators=[DataRequired(), Length(max=190),
        Regexp(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", message="Email chưa đúng định dạng.")])
    phone = StringField("Số điện thoại", validators=[DataRequired(), Length(max=30)])
    address = StringField("Địa chỉ giao hàng", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=12, max=128)])
    confirm_password = PasswordField("Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Tạo tài khoản")


class CheckoutForm(FlaskForm):
    submit = SubmitField("Đặt hàng")


class ProfileForm(FlaskForm):
    full_name = StringField("Họ và tên", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Length(max=190),
        Regexp(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", message="Email chưa đúng định dạng.")])
    phone = StringField("Số điện thoại", validators=[DataRequired(), Length(max=30)])
    address = StringField("Địa chỉ giao hàng", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("Lưu hồ sơ")
