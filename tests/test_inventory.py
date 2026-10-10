"""Real MySQL transaction, state, role and concurrent stock invariants."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Product, PurchaseReceipt, SalesOrder, StockMovement, AuditLog, User, Business
from app.services.inventory_service import InventoryError, money
from app.services.transaction_service import create_document as service_create, transition as service_transition
from test_auth import account, auth_client, csrf, login


def create_document(*args, **kwargs):
    # Service commits on a separate connection. End the assertion session's old
    # REPEATABLE READ snapshot before observing its result.
    db.session.rollback()
    return service_create(*args, **kwargs)


def transition(*args, **kwargs):
    db.session.rollback()
    return service_transition(*args, **kwargs)


def lines(catalog, qty=5, cost='1234.56'):
    return [dict(product_id=catalog['product_id'],quantity=qty,unit_cost=cost)]


def receipt(account,catalog,qty=5,complete=False):
    identifier=create_document('purchases',account['id'],dict(business_id=catalog['business_id']),lines(catalog,qty))
    if complete:
        transition('purchases',account['id'],identifier,'complete')
    return identifier


def order(account,catalog,qty=2):
    return create_document('sales',account['id'],dict(customer_name='Khách thử nghiệm'),lines(catalog,qty,'0.01'))


def stock(catalog):
    db.session.rollback()
    return db.session.get(Product,catalog['product_id']).stock_quantity


def movements(catalog):
    return db.session.scalars(select(StockMovement).where(StockMovement.product_id==catalog['product_id']).order_by(StockMovement.id)).all()


def test_purchase_lifecycle(account,catalog):
    identifier=receipt(account,catalog)
    assert stock(catalog)==0 and not movements(catalog)
    record=db.session.get(PurchaseReceipt,identifier)
    assert record.status=='draft' and record.total_amount==Decimal('6172.80')
    transition('purchases',account['id'],identifier,'complete')
    assert stock(catalog)==5 and movements(catalog)[0].movement_type=='purchase_in'
    with pytest.raises(InventoryError):transition('purchases',account['id'],identifier,'complete')
    assert stock(catalog)==5 and len(movements(catalog))==1
    transition('purchases',account['id'],identifier,'cancel')
    assert stock(catalog)==0 and len(movements(catalog))==2
    assert movements(catalog)[-1].quantity_delta==-5 and movements(catalog)[-1].movement_type=='adjustment'
    with pytest.raises(InventoryError):transition('purchases',account['id'],identifier,'cancel')
    assert stock(catalog)==0 and len(movements(catalog))==2
    actions=db.session.scalars(select(AuditLog.action).where(AuditLog.entity_type=='purchase_receipts',AuditLog.entity_id==identifier)).all()
    assert actions==['create_draft','complete','cancel']


def test_acceptance_purchase_sale_return_ledger(account,catalog):
    """Acceptance: exact ledger after every step, including failed reversal."""
    def check(expected_stock, deltas):
        assert stock(catalog) == expected_stock
        assert [row.quantity_delta for row in movements(catalog)] == deltas

    incoming = receipt(account,catalog,5)
    check(0, [])
    transition('purchases',account['id'],incoming,'complete')
    check(5, [5])
    outgoing = order(account,catalog,4)
    check(5, [5])
    transition('sales',account['id'],outgoing,'complete')
    check(1, [5,-4])
    with pytest.raises(InventoryError):
        transition('purchases',account['id'],incoming,'cancel')
    check(1, [5,-4])
    assert db.session.get(PurchaseReceipt,incoming).status == 'completed'
    transition('sales',account['id'],outgoing,'cancel')
    check(5, [5,-4,4])
    transition('purchases',account['id'],incoming,'cancel')
    check(0, [5,-4,4,-5])
    assert [row.movement_type for row in movements(catalog)] == [
        'purchase_in','sale_out','sale_return','adjustment']
    for kind,identifier in [('sales',outgoing),('purchases',incoming)]:
        with pytest.raises(InventoryError):
            transition(kind,account['id'],identifier,'cancel')
        check(0, [5,-4,4,-5])


def test_sales_snapshot_return_once(account,catalog):
    receipt(account,catalog,5,True)
    identifier=order(account,catalog,2)
    assert stock(catalog)==5 and len(movements(catalog))==1
    record=db.session.get(SalesOrder,identifier)
    assert record.items[0].unit_price==Decimal('2345.67') and record.total_amount==Decimal('4691.34')
    product=db.session.get(Product,catalog['product_id']);product.selling_price=Decimal('9999.99');db.session.commit()
    transition('sales',account['id'],identifier,'complete')
    assert stock(catalog)==3 and movements(catalog)[-1].movement_type=='sale_out'
    assert db.session.get(SalesOrder,identifier).total_amount==Decimal('4691.34')
    with pytest.raises(InventoryError):transition('sales',account['id'],identifier,'complete')
    transition('sales',account['id'],identifier,'cancel')
    assert stock(catalog)==5 and movements(catalog)[-1].movement_type=='sale_return'
    with pytest.raises(InventoryError):transition('sales',account['id'],identifier,'cancel')
    assert stock(catalog)==5 and len(movements(catalog))==3


@pytest.mark.parametrize('kind',['purchases','sales'])
def test_draft_cancel_has_no_movements(account,catalog,kind):
    if kind=='sales':receipt(account,catalog,5,True)
    before=stock(catalog); count=len(movements(catalog))
    identifier=receipt(account,catalog) if kind=='purchases' else order(account,catalog)
    transition(kind,account['id'],identifier,'cancel')
    assert stock(catalog)==before and len(movements(catalog))==count
    with pytest.raises(InventoryError):transition(kind,account['id'],identifier,'complete')


def test_oversell_and_purchase_cancel_insufficient(account,catalog):
    incoming=receipt(account,catalog,5,True)
    with pytest.raises(InventoryError):order(account,catalog,6)
    sale=order(account,catalog,4);transition('sales',account['id'],sale,'complete')
    with pytest.raises(InventoryError):transition('purchases',account['id'],incoming,'cancel')
    assert stock(catalog)==1 and len(movements(catalog))==2
    assert db.session.get(PurchaseReceipt,incoming).status=='completed'


@pytest.mark.parametrize('value',['-1','NaN','Infinity','0.001','1000000000000',1.2,True])
def test_money_rejects_invalid(value):
    with pytest.raises(InventoryError):money(value)


@pytest.mark.parametrize('qty',[0,-1,'1.5','2e2',2147483648])
def test_invalid_quantity_atomic(account,catalog,qty):
    with pytest.raises(InventoryError):receipt(account,catalog,qty)
    assert stock(catalog)==0 and not movements(catalog)


def test_duplicate_rows_and_overflow(account,catalog):
    with pytest.raises(InventoryError):create_document('purchases',account['id'],dict(business_id=catalog['business_id']),lines(catalog)+lines(catalog))
    with pytest.raises(InventoryError):create_document('purchases',account['id'],dict(business_id=catalog['business_id']),lines(catalog,2,'999999999999.99'))
    assert stock(catalog)==0


def test_duplicate_creation_code(account,catalog):
    code='PN-TEST-'+catalog['suffix']
    first=create_document('purchases',account['id'],dict(business_id=catalog['business_id']),lines(catalog),code)
    with pytest.raises(InventoryError):create_document('purchases',account['id'],dict(business_id=catalog['business_id']),lines(catalog),code)
    assert db.session.scalar(select(func.count()).select_from(PurchaseReceipt).where(PurchaseReceipt.receipt_code==code))==1
    assert db.session.get(PurchaseReceipt,first).status=='draft'


@pytest.mark.parametrize('kind,action',[('purchases','complete'),('purchases','cancel'),('sales','complete'),('sales','cancel')])
def test_failure_after_writes_rolls_back_everything(account,catalog,monkeypatch,kind,action):
    import app.services.transaction_service as service
    if kind=='sales':receipt(account,catalog,5,True)
    identifier=receipt(account,catalog) if kind=='purchases' else order(account,catalog)
    if action=='cancel':transition(kind,account['id'],identifier,'complete')
    before=stock(catalog); count=len(movements(catalog))
    before_audits=db.session.scalar(select(func.count()).select_from(AuditLog))
    model=PurchaseReceipt if kind=='purchases' else SalesOrder
    state=db.session.get(model,identifier).status
    def fail_after_flush(session,*args):
        session.flush()  # prove rollback even after UPDATE/INSERT SQL reaches MySQL
        raise SQLAlchemyError('injected test failure')
    monkeypatch.setattr(service,'audit',fail_after_flush)
    with pytest.raises(InventoryError):transition(kind,account['id'],identifier,action)
    assert stock(catalog)==before and len(movements(catalog))==count
    assert db.session.get(model,identifier).status==state
    assert db.session.scalar(select(func.count()).select_from(AuditLog))==before_audits


@pytest.mark.parametrize('scenario',['oversell','same-sale','cancel-sale','same-purchase','cancel-purchase'])
def test_real_concurrent_requests(mysql_app,account,catalog,scenario):
    incoming=receipt(account,catalog,5,True)
    if scenario=='same-purchase':
        identifier=receipt(account,catalog,2);jobs=[('purchases',identifier,'complete')]*2;expected=7
    elif scenario=='cancel-purchase':
        jobs=[('purchases',incoming,'cancel')]*2;expected=0
    else:
        first=order(account,catalog,4)
        if scenario=='cancel-sale':
            transition('sales',account['id'],first,'complete');jobs=[('sales',first,'cancel')]*2;expected=5
        else:
            second=order(account,catalog,4) if scenario=='oversell' else first
            jobs=[('sales',first,'complete'),('sales',second,'complete')];expected=1
    db.session.remove()
    barrier=Barrier(2)
    def worker(job):
        with mysql_app.app_context():
            barrier.wait(timeout=10)
            try:transition(job[0],account['id'],job[1],job[2]);return 'ok'
            except InventoryError:return 'rejected'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(worker,jobs))
    assert sorted(results)==['ok','rejected']
    assert stock(catalog)==expected


def test_inactive_product_and_supplier(account,catalog):
    product=db.session.get(Product,catalog['product_id']);product.is_active=False;db.session.commit()
    with pytest.raises(InventoryError):receipt(account,catalog)
    product.is_active=True;db.session.get(Business,catalog['business_id']).is_active=False;db.session.commit()
    with pytest.raises(InventoryError):receipt(account,catalog)


def test_staff_service_scope(account,catalog):
    receipt(account,catalog,5,True)
    own=order(account,catalog)
    staff_id=catalog['user_id']
    with pytest.raises(InventoryError) as error:receipt(dict(id=staff_id),catalog)
    assert error.value.status==403
    with pytest.raises(InventoryError):transition('sales',staff_id,own,'complete')
    staff_order=order(dict(id=staff_id),catalog)
    transition('sales',staff_id,staff_order,'complete')
    with pytest.raises(InventoryError):transition('sales',staff_id,staff_order,'cancel')
    transition('sales',account['id'],staff_order,'cancel')


def test_stock_overflow_rejected(account,catalog):
    identifier=receipt(account,catalog,1)
    product=db.session.get(Product,catalog['product_id']);product.stock_quantity=4294967295;db.session.commit()
    with pytest.raises(InventoryError):transition('purchases',account['id'],identifier,'complete')
    assert stock(catalog)==4294967295 and not movements(catalog)


def test_multi_product_insufficiency_rolls_back_first_line(account,catalog):
    from app.models import Category
    second=Product(sku='SECOND-'+catalog['suffix'],name='Second test product',category_id=catalog['category_id'],
        purchase_price=Decimal('0.01'),selling_price=Decimal('0.02'),stock_quantity=0,reorder_level=1)
    db.session.add(second);db.session.commit();second_id=second.id
    identifier=create_document('purchases',account['id'],dict(business_id=catalog['business_id']),
        lines(catalog,5)+[dict(product_id=second_id,quantity=2,unit_cost='0.01')])
    transition('purchases',account['id'],identifier,'complete')
    sale=create_document('sales',account['id'],dict(customer_name='Test multi product'),
        lines(catalog,4)+[dict(product_id=second_id,quantity=2)])
    other=create_document('sales',account['id'],dict(customer_name='Second buyer'),[dict(product_id=second_id,quantity=1)])
    transition('sales',account['id'],other,'complete')
    with pytest.raises(InventoryError):transition('sales',account['id'],sale,'complete')
    assert stock(catalog)==5
    assert db.session.get(Product,second_id).stock_quantity==1
    assert db.session.get(SalesOrder,sale).status=='draft'
    assert not db.session.scalar(select(StockMovement.id).where(StockMovement.reference_type=='sales_order',StockMovement.reference_id==sale))


def test_create_draft_failure_rolls_back_header_items_and_audit(account,catalog,monkeypatch):
    import app.services.transaction_service as service
    code='ROLLBACK-'+catalog['suffix']
    def fail(session,*args):
        session.flush()
        raise SQLAlchemyError('injected')
    monkeypatch.setattr(service,'audit',fail)
    with pytest.raises(InventoryError):create_document('purchases',account['id'],dict(business_id=catalog['business_id']),lines(catalog),code)
    db.session.rollback()
    assert not db.session.scalar(select(PurchaseReceipt.id).where(PurchaseReceipt.receipt_code==code))
    assert stock(catalog)==0 and not movements(catalog)


@pytest.mark.parametrize('cost',['0','0.01','999999999999.99'])
def test_mysql_money_roundtrip(account,catalog,cost):
    identifier=create_document('purchases',account['id'],dict(business_id=catalog['business_id']),lines(catalog,1,cost))
    db.session.rollback()
    record=db.session.get(PurchaseReceipt,identifier)
    assert record.total_amount==Decimal(cost) and record.items[0].unit_cost==Decimal(cost)


def test_completion_rejects_inactive_but_reversal_remains_possible(account,catalog):
    incoming=receipt(account,catalog,5,True)
    sale=order(account,catalog,2)
    product=db.session.get(Product,catalog['product_id']);product.is_active=False;db.session.commit()
    with pytest.raises(InventoryError):transition('sales',account['id'],sale,'complete')
    transition('purchases',account['id'],incoming,'cancel')
    assert stock(catalog)==0


def test_inactive_actor_cannot_write(account,catalog):
    user=db.session.get(User,account['id']);user.is_active=False;db.session.commit()
    with pytest.raises(InventoryError) as error:receipt(account,catalog)
    assert error.value.status==403
