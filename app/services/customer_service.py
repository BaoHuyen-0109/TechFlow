"""Customer validation, atomic profile changes and minimal history projections."""
import re
from decimal import Decimal

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models import Customer, SalesOrder, SalesOrderItem, Product
from app.models import AuditLog
from app.services.inventory_service import InventoryError, actor_for


class DuplicateCustomer(InventoryError):
    def __init__(self, customer_id=None):
        super().__init__('Số điện thoại đã có hồ sơ (kể cả ngừng hoạt động). Hãy chọn hồ sơ có sẵn hoặc bán vãng lai.', 409)
        self.customer_id = customer_id


def normalize_registered_profile(data):
    """Validate a self-service profile and expose safe validation feedback."""
    try:
        return validated_profile(data)
    except InventoryError as error:
        raise ValueError(error.message) from None


def customer_audit(session, actor_id, action, identifier):
    session.add(AuditLog(user_id=actor_id,action=action,entity_type='customers',entity_id=identifier,
                        description='Thay đổi hồ sơ khách hàng; không ghi thông tin liên hệ'))


def normalize_phone(value):
    raw = str(value or '').strip()
    if not re.fullmatch(r'\+?[0-9 ()\-.]+', raw, flags=re.ASCII):
        raise InventoryError('Số điện thoại Việt Nam chưa đúng định dạng.', 422)
    digits = re.sub(r'[ ()\-.]', '', raw)
    if digits.startswith('+84'):
        digits = '0'+digits[3:]
    elif digits.startswith('84'):
        digits = '0'+digits[2:]
    if not re.fullmatch(r'0[1-9][0-9]{8,9}', digits, flags=re.ASCII):
        raise InventoryError('Nhập số Việt Nam 10–11 chữ số bắt đầu bằng 0, hoặc dạng +84 tương ứng.', 422)
    return '+84'+digits[1:]


def validated_profile(data):
    result = {}
    for field, maximum in [('name',150),('email',190),('address',255)]:
        value = str(data.get(field) or '').strip()
        if len(value) > maximum or (field == 'name' and not value) or any(ord(c)<32 for c in value):
            raise InventoryError('Thông tin khách hàng không hợp lệ.', 422)
        result[field] = value or None
    if result['email'] and not re.fullmatch(r'[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+', result['email']):
        raise InventoryError('Email chưa đúng định dạng.', 422)
    result['phone'] = normalize_phone(data.get('phone'))
    return result


def insert_customer(session, actor, data):
    """Caller owns transaction, allowing new customer + order to commit together."""
    values = validated_profile(data)
    existing = session.scalar(select(Customer.id).where(Customer.phone == values['phone']))
    if existing:
        raise DuplicateCustomer(existing)
    customer = Customer(**values, created_by=actor.id)
    session.add(customer)
    session.flush()
    customer_audit(session, actor.id, 'create', customer.id)
    return customer


def save_customer(actor_id, data, identifier=None):
    try:
        with Session(db.engine) as session, session.begin():
            actor = actor_for(session, actor_id)
            if actor.role != 'admin':
                raise InventoryError('Chỉ quản trị viên được quản lý hồ sơ khách hàng.', 403)
            if identifier is None:
                customer = insert_customer(session, actor, data)
            else:
                customer = session.scalar(select(Customer).where(Customer.id == identifier).with_for_update())
                if not customer:
                    raise InventoryError('Không tìm thấy khách hàng.',404)
                values = validated_profile(data)
                other = session.scalar(select(Customer.id).where(Customer.phone == values['phone'], Customer.id != identifier))
                if other:
                    raise DuplicateCustomer(other)
                for field,value in values.items():
                    setattr(customer,field,value)
                customer_audit(session,actor.id,'update',customer.id)
            result = customer.id
        return result
    except IntegrityError:
        raise DuplicateCustomer() from None
    except SQLAlchemyError:
        raise InventoryError('Chưa thể xác nhận kết quả lưu. Kiểm tra danh sách trước khi thử lại.',503) from None


def set_active(actor_id, identifier, active):
    try:
        with Session(db.engine) as session, session.begin():
            actor = actor_for(session,actor_id)
            if actor.role != 'admin':
                raise InventoryError('Chỉ quản trị viên được đổi trạng thái khách hàng.',403)
            customer = session.scalar(select(Customer).where(Customer.id == identifier).with_for_update())
            if not customer:
                raise InventoryError('Không tìm thấy khách hàng.',404)
            if customer.is_active != active:
                customer.is_active = active
                customer_audit(session,actor.id,'activate' if active else 'deactivate',identifier)
    except SQLAlchemyError:
        raise InventoryError('Chưa thể xác nhận kết quả đổi trạng thái. Vui lòng tải lại.',503) from None


def customer_query(q='', active_only=False):
    query = select(Customer)
    if active_only:
        query = query.where(Customer.is_active.is_(True))
    if q:
        phone_term = re.sub(r'[ ()\-.]', '', q)
        if phone_term.startswith('+84'): phone_term = phone_term[3:]
        elif phone_term.startswith('84'): phone_term = phone_term[2:]
        elif phone_term.startswith('0'): phone_term = phone_term[1:]
        matches = [Customer.name.contains(q,autoescape=True), Customer.email.contains(q,autoescape=True)]
        if phone_term and phone_term.isascii() and phone_term.isdigit():
            matches.append(Customer.phone.contains(phone_term,autoescape=True))
        query = query.where(or_(*matches))
    return query


def purchase_history(identifier, actor, page=1, product_page=1):
    """Select only consulting fields; never return notes/audit/owner details."""
    completed = (SalesOrder.customer_id == identifier, SalesOrder.status == 'completed')
    count,total,last = db.session.execute(select(func.count(SalesOrder.id),
        func.coalesce(func.sum(SalesOrder.total_amount),0),func.max(SalesOrder.order_date)).where(*completed)).one()
    query = select(SalesOrder.id,SalesOrder.order_code,SalesOrder.order_date,
                   SalesOrder.status,SalesOrder.total_amount,SalesOrder.created_by).where(SalesOrder.customer_id == identifier)
    if actor.role != 'admin':
        query = query.where(SalesOrder.status == 'completed')
    order_count = db.session.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.session.execute(query.order_by(SalesOrder.order_date.desc(),SalesOrder.id.desc()).offset((page-1)*10).limit(10)).mappings().all()
    order_ids = [row['id'] for row in rows]
    items = db.session.execute(select(SalesOrderItem.order_id, Product.name,Product.sku,
        SalesOrderItem.quantity,SalesOrderItem.unit_price,SalesOrderItem.line_total)
        .join(Product,Product.id == SalesOrderItem.product_id).where(SalesOrderItem.order_id.in_(order_ids))
        .order_by(SalesOrderItem.id)).mappings().all() if order_ids else []
    grouped = {order_id:[] for order_id in order_ids}
    for item in items: grouped[item['order_id']].append(item)
    product_query = select(Product.id,Product.name,Product.sku,func.sum(SalesOrderItem.quantity).label('quantity'),
        func.sum(SalesOrderItem.line_total).label('spent')).join(SalesOrderItem,SalesOrderItem.product_id == Product.id)
    product_query = product_query.join(SalesOrder,SalesOrder.id == SalesOrderItem.order_id).where(*completed)
    product_query = product_query.group_by(Product.id,Product.name,Product.sku)
    product_count = db.session.scalar(select(func.count()).select_from(product_query.subquery()))
    products = db.session.execute(product_query.order_by(Product.name,Product.id).offset((product_page-1)*10).limit(10)).mappings().all()
    return dict(count=count,total=Decimal(total),last=last,order_count=order_count,rows=rows,items=grouped,
                page=page,products=products,product_count=product_count,product_page=product_page)
