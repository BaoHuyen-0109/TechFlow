from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app.auth.permissions import business_required
from app.extensions import db
from app.models import Customer
from app.customers.forms import CustomerForm
from app.purchases.forms import ActionForm
from app.services.customer_service import customer_query, purchase_history, save_customer, set_active, DuplicateCustomer
from app.services.inventory_service import InventoryError

blueprint = Blueprint('customers',__name__,url_prefix='/business/customers')


def admin_only():
    if current_user.role != 'admin': abort(403)


def context(**values):
    return dict(active_page='customers',workspace_home=url_for('dashboard.staff'),**values)


def page_number(key='page'):
    try:
        value = int(request.args.get(key,1))
        if not 1 <= value <= 2147483647: raise ValueError
        return value
    except ValueError:
        abort(400)


def record(identifier):
    customer = db.session.get(Customer,identifier)
    if not customer: abort(404)
    return customer


@blueprint.get('')
@business_required
def index():
    q = request.args.get('q','').strip()
    state = request.args.get('status','')
    if len(q)>120 or state not in {'','active','inactive'}: abort(400)
    query = customer_query(q)
    if state: query = query.where(Customer.is_active.is_(state == 'active'))
    results = db.paginate(query.order_by(Customer.id.desc()),page=page_number(),per_page=10,error_out=False)
    return render_template('customers/index.html',**context(results=results))


@blueprint.get('/search')
@business_required
def search():
    q = request.args.get('q','').strip()
    if len(q)>120: abort(400)
    if len(q)<2: return jsonify([])
    rows = db.session.scalars(customer_query(q,active_only=True).order_by(Customer.name,Customer.id).limit(20)).all()
    return jsonify([dict(id=c.id,name=c.name,phone=c.phone,email=c.email or '',address=c.address or '',
                         history_url=url_for('customers.detail',customer_id=c.id)) for c in rows])


@blueprint.get('/<int:customer_id>')
@business_required
def detail(customer_id):
    customer = record(customer_id)
    history = purchase_history(customer_id,current_user,page_number(),page_number('product_page'))
    return render_template('customers/detail.html',**context(customer=customer,history=history,form=ActionForm()))


@blueprint.route('/new',methods=['GET','POST'])
@blueprint.route('/<int:customer_id>/edit',methods=['GET','POST'])
@business_required
def edit(customer_id=None):
    admin_only()
    customer = record(customer_id) if customer_id else None
    form = CustomerForm(obj=customer)
    message,duplicate_id,status = None,None,200
    if form.validate_on_submit():
        try:
            identifier = save_customer(current_user.id,form.data,customer_id)
            db.session.rollback()
            flash('Đã lưu hồ sơ khách hàng. Snapshot đơn cũ được giữ nguyên.','success')
            return redirect(url_for('customers.detail',customer_id=identifier),code=303)
        except InventoryError as error:
            message,status = error.message,error.status
            if isinstance(error,DuplicateCustomer): duplicate_id = error.customer_id
    elif request.method == 'POST':
        message,status = 'Vui lòng kiểm tra các trường được đánh dấu.',422
    return render_template('customers/form.html',**context(customer=customer,form=form,message=message,duplicate_id=duplicate_id)),status


@blueprint.post('/<int:customer_id>/<action>')
@business_required
def change_status(customer_id,action):
    admin_only()
    record(customer_id)
    if action not in {'activate','deactivate'}: abort(404)
    if not ActionForm().validate_on_submit(): abort(400)
    try:
        set_active(current_user.id,customer_id,action == 'activate')
        flash('Đã cập nhật trạng thái. Đơn hàng và lịch sử vẫn được giữ lại.','success')
    except InventoryError as error:
        db.session.rollback()
        return render_template('customers/detail.html',**context(customer=record(customer_id),
            history=purchase_history(customer_id,current_user),form=ActionForm(),message=error.message)),error.status
    db.session.rollback()
    return redirect(url_for('customers.detail',customer_id=customer_id),code=303)
