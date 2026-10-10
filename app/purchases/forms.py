"""Shared transaction forms; all authoritative amounts are computed by services."""
from flask_wtf import FlaskForm
from wtforms import Form, FieldList, FormField, SelectField, IntegerField, DecimalField, StringField, TextAreaField, HiddenField
from wtforms.validators import InputRequired, Length, NumberRange, Optional
from app.catalog.forms import email, phone, clean, MoneyField, price


class LineForm(Form):
    product_id = SelectField('Sản phẩm', coerce=int, validate_choice=False, validators=[InputRequired(message='Vui lòng chọn sản phẩm.')])
    quantity = IntegerField('Số lượng', validators=[InputRequired(message='Vui lòng nhập số lượng.'), NumberRange(min=1, max=2147483647, message='Số lượng phải là số nguyên từ 1 đến 2.147.483.647.')])
    unit_cost = MoneyField('Đơn giá nhập (VND)', places=None, validators=[Optional(), price])


class TransactionForm(FlaskForm):
    ticket = HiddenField(validators=[InputRequired()])
    business_id = SelectField('Nhà cung cấp', coerce=int, validate_choice=False, validators=[Optional()])
    customer_name = StringField('Tên khách hàng', validators=[Optional(), Length(max=150)])
    customer_phone = StringField('Số điện thoại', filters=[clean], validators=[Optional(), Length(max=30), phone])
    customer_email = StringField('Email', filters=[clean], validators=[Optional(), Length(max=190), email])
    customer_address = StringField('Địa chỉ', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Ghi chú', validators=[Optional(), Length(max=2000)])
    lines = FieldList(FormField(LineForm), min_entries=1, max_entries=50)


class ActionForm(FlaskForm):
    pass
