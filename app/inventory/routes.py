from flask import Blueprint, abort, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload

from app.auth.permissions import business_required
from app.extensions import db
from app.models import StockMovement, Product, SalesOrder, User

blueprint = Blueprint('inventory',__name__,url_prefix='/business/inventory')


@blueprint.get('')
@business_required
def index():
    query = select(StockMovement).join(Product).options(joinedload(StockMovement.product))
    if current_user.role != 'admin':
        client_ids = select(User.id).where(User.role == 'client')
        query = query.where(StockMovement.reference_type == 'sales_order',
            StockMovement.reference_id.in_(select(SalesOrder.id).where(
                (SalesOrder.created_by == current_user.id) | SalesOrder.created_by.in_(client_ids))))
    q = request.args.get('q','').strip()
    kind = request.args.get('type','')
    if len(q) > 120 or kind not in {'','purchase_in','sale_out','sale_return','adjustment'}:
        abort(400)
    if q:
        query = query.where(or_(Product.sku.contains(q,autoescape=True),Product.name.contains(q,autoescape=True)))
    if kind:
        query = query.where(StockMovement.movement_type == kind)
    try:
        page=int(request.args.get('page',1))
        if not 1 <= page <= 2147483647:
            raise ValueError
    except ValueError:
        abort(400)
    results=db.paginate(query.order_by(StockMovement.id.desc()),page=page,per_page=20,error_out=False)
    return render_template('transactions/movements.html',results=results,active_page='inventory',workspace_home=url_for('dashboard.staff'))
