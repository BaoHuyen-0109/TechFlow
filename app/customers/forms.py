from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import InputRequired, Length, Optional
from app.catalog.forms import clean, email


class CustomerForm(FlaskForm):
    name = StringField('Tên khách hàng',filters=[clean],validators=[InputRequired(message='Vui lòng nhập tên khách hàng.'),Length(max=150,message='Tên tối đa 150 ký tự.')])
    phone = StringField('Số điện thoại Việt Nam',filters=[clean],validators=[InputRequired(message='Vui lòng nhập số điện thoại.'),Length(max=30,message='Số điện thoại tối đa 30 ký tự trước chuẩn hóa.')])
    email = StringField('Email',filters=[clean],validators=[Optional(),Length(max=190,message='Email tối đa 190 ký tự.'),email])
    address = TextAreaField('Địa chỉ',filters=[clean],validators=[Optional(),Length(max=255,message='Địa chỉ tối đa 255 ký tự.')])
