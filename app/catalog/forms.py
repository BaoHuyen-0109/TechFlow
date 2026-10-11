import re
from decimal import Decimal
from urllib.parse import urlsplit

from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, FileField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, Optional, ValidationError, NumberRange


def clean(value):
    return value.strip() if isinstance(value, str) else value


def identifier(form, field):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", field.data or ""):
        raise ValidationError("Mã chỉ gồm chữ không dấu, số và các ký tự . _ / -.")
    field.data = field.data.upper()


def price(form, field):
    value = field.data
    if value is None or not value.is_finite() or value < 0 or value > Decimal("999999999999.99"):
        raise ValidationError("Giá phải từ 0 đến 999.999.999.999,99.")
    if value != value.quantize(Decimal("0.01")):
        raise ValidationError("Giá chỉ có tối đa hai chữ số thập phân.")


def email(form, field):
    if not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", field.data):
        raise ValidationError("Email chưa đúng định dạng.")


def phone(form, field):
    if not re.fullmatch(r"\+?[0-9 ()\-.]+", field.data) or not 7 <= sum(c.isdigit() for c in field.data) <= 15:
        raise ValidationError("Số điện thoại cần có 7–15 chữ số.")


def image_url(form, field):
    try:
        parts = urlsplit(field.data)
        valid = parts.scheme in {"http", "https"} and parts.hostname and not parts.username and not parts.password
        valid = valid and not any(c.isspace() or ord(c) < 32 for c in field.data)
        _ = parts.port
    except ValueError:
        valid = False
    if not valid:
        raise ValidationError("Ảnh cần là URL HTTP/HTTPS hợp lệ, không chứa thông tin đăng nhập.")


def text(label, maximum, required=False, **kwargs):
    return StringField(label, filters=[clean], validators=[DataRequired(message="Vui lòng nhập thông tin.") if required else Optional(), Length(max=maximum, message=f"Tối đa {maximum} ký tự.")], **kwargs)


class MoneyField(DecimalField):
    def process_formdata(self, values):
        try:
            super().process_formdata(values)
        except ValueError:
            raise ValueError("Vui lòng nhập số; dùng dấu chấm cho phần thập phân.") from None


class ChoiceField(SelectField):
    def process_formdata(self, values):
        try:
            super().process_formdata(values)
        except ValueError:
            raise ValueError("Lựa chọn chưa hợp lệ.") from None

    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError:
            raise ValidationError("Vui lòng chọn dữ liệu tồn tại trong danh sách.") from None


class CountField(IntegerField):
    def process_formdata(self, values):
        try:
            super().process_formdata(values)
        except ValueError:
            raise ValueError("Vui lòng nhập số nguyên.") from None


class CategoryForm(FlaskForm):
    code = StringField("Mã danh mục", filters=[clean], validators=[DataRequired(message="Vui lòng nhập mã."), Length(max=30, message="Tối đa 30 ký tự."), identifier])
    name = text("Tên danh mục", 100, True)
    description = TextAreaField("Mô tả", filters=[clean], validators=[Optional(), Length(max=4000, message="Tối đa 4000 ký tự.")])
    is_active = BooleanField("Đang hoạt động", default=True)


class BusinessForm(FlaskForm):
    code = StringField("Mã nhà cung cấp", filters=[clean], validators=[InputRequired(message="Vui lòng nhập mã."), Length(max=30, message="Tối đa 30 ký tự."), identifier])
    name = text("Tên nhà cung cấp", 180, True)
    tax_code = text("Mã số thuế", 30)
    contact_person = text("Người liên hệ", 120)
    email = StringField("Email", filters=[clean], validators=[Optional(), Length(max=190, message="Tối đa 190 ký tự."), email])
    phone = StringField("Điện thoại", filters=[clean], validators=[Optional(), Length(max=30, message="Tối đa 30 ký tự."), phone])
    address = text("Địa chỉ", 255)
    notes = TextAreaField("Ghi chú", filters=[clean], validators=[Optional(), Length(max=4000, message="Tối đa 4000 ký tự.")])
    is_active = BooleanField("Đang hoạt động", default=True)


class ProductForm(FlaskForm):
    image_file = FileField("Chọn hoặc thả ảnh sản phẩm", validators=[Optional()])
    remove_image = BooleanField("Gỡ ảnh hiện tại")
    warranty_enabled = BooleanField('Có bảo hành', default=False)
    warranty_months = CountField('Thời hạn bảo hành (tháng)', validators=[Optional(), NumberRange(min=1,max=120,message='Từ 1 đến 120 tháng.')])
    warranty_notes = TextAreaField('Điều kiện và ghi chú bảo hành', filters=[clean], validators=[Optional(),Length(max=2000,message='Tối đa 2000 ký tự.')])

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators)
        # Optional stops field validators for an empty month, so check explicitly.
        if self.warranty_enabled.data and self.warranty_months.data is None:
            self.warranty_months.errors = list(self.warranty_months.errors) + ['Vui lòng nhập thời hạn khi bật bảo hành.']
            valid = False
        if not self.warranty_enabled.data:
            self.warranty_months.data = None
        return valid

    sku = StringField("Mã SKU", filters=[clean], validators=[InputRequired(message="Vui lòng nhập mã SKU."), Length(max=50, message="Tối đa 50 ký tự."), identifier])
    name = text("Tên sản phẩm", 180, True)
    category_id = ChoiceField("Danh mục", coerce=int, validators=[InputRequired(message="Vui lòng chọn danh mục."), NumberRange(min=1, message="Vui lòng chọn danh mục.")])
    business_id = ChoiceField("Nhà cung cấp", coerce=int)
    brand = text("Thương hiệu", 100)
    model = text("Model", 100)
    purchase_price = MoneyField("Giá nhập (VND)", places=None, validators=[InputRequired(message="Vui lòng nhập giá."), price])
    selling_price = MoneyField("Giá bán (VND)", places=None, validators=[InputRequired(message="Vui lòng nhập giá."), price])
    reorder_level = CountField("Ngưỡng cảnh báo tồn kho", default=5, validators=[InputRequired(message="Vui lòng nhập ngưỡng cảnh báo."), NumberRange(min=0, max=4294967295, message="Giá trị phải từ 0 đến 4294967295.")])
    image_url = StringField("URL hình ảnh", filters=[clean], validators=[Optional(), Length(max=500, message="Tối đa 500 ký tự."), image_url])
    description = TextAreaField("Mô tả", filters=[clean], validators=[Optional(), Length(max=4000, message="Tối đa 4000 ký tự.")])
    is_active = BooleanField("Đang hoạt động", default=True)
