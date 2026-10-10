from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField, HiddenField
from wtforms.validators import InputRequired, Length, Optional, NumberRange
from app.catalog.forms import ChoiceField, CountField


class LocalDateField(DateField):
    def process_formdata(self, values):
        try:
            super().process_formdata(values)
        except ValueError:
            raise ValueError('Ngày chưa hợp lệ. Vui lòng chọn ngày trên lịch.') from None


class IntakeForm(FlaskForm):
    ticket = HiddenField(validators=[InputRequired()])
    unit_index = CountField('Thiết bị thứ',default=1,validators=[InputRequired(message='Nhập vị trí thiết bị.'),NumberRange(min=1,max=2147483647,message='Vị trí thiết bị không hợp lệ.')])
    serial = StringField('Serial / IMEI (nếu có)',validators=[Optional(),Length(max=100,message='Tối đa 100 ký tự.')])
    issue = TextAreaField('Lỗi khách hàng báo',validators=[InputRequired(message='Vui lòng mô tả lỗi.'),Length(max=2000,message='Tối đa 2000 ký tự.')])
    promised_on = LocalDateField('Ngày hẹn trả',validators=[Optional()],format='%Y-%m-%d')


class HandlingForm(FlaskForm):
    expected_status = HiddenField(validators=[InputRequired()])
    target = ChoiceField('Thao tác',choices=[('processing','Chấp nhận và bắt đầu xử lý'),('completed','Hoàn thành xử lý'),('rejected','Từ chối'),('returned','Đã trả khách')])
    inspection_result = TextAreaField('Kết quả kiểm tra / xử lý',validators=[Optional(),Length(max=2000,message='Tối đa 2000 ký tự.')])
    rejection_reason = TextAreaField('Lý do từ chối',validators=[Optional(),Length(max=1000,message='Tối đa 1000 ký tự.')])
    note = TextAreaField('Ghi chú xử lý',validators=[Optional(),Length(max=2000,message='Tối đa 2000 ký tự.')])
    confirmed = ChoiceField('Xác nhận thao tác',choices=[('','Chưa xác nhận'),('yes','Tôi đã kiểm tra và đồng ý thao tác')],validators=[InputRequired(message='Vui lòng xác nhận thao tác.')])


class AssignmentForm(FlaskForm):
    expected_status = HiddenField(validators=[InputRequired()])
    assignee = ChoiceField('Người phụ trách',coerce=int)


class LegacyForm(FlaskForm):
    starts_on = LocalDateField('Ngày bắt đầu đã xác minh',validators=[InputRequired(message='Nhập ngày bắt đầu.')])
    months = CountField('Thời hạn (tháng)',validators=[InputRequired(message='Nhập thời hạn bảo hành.'),NumberRange(min=1,max=120,message='Từ 1 đến 120 tháng.')])
    reason = TextAreaField('Căn cứ xác minh chính sách',validators=[InputRequired(message='Ghi căn cứ xác minh.'),Length(max=1000,message='Tối đa 1000 ký tự.')])
    notes = TextAreaField('Điều kiện bảo hành',validators=[Optional(),Length(max=2000,message='Tối đa 2000 ký tự.')])
