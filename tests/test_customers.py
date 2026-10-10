"""Real MySQL customer identity, snapshot, atomicity and consulting permissions."""
import secrets
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal

import pytest
from sqlalchemy import select,func
from sqlalchemy.exc import SQLAlchemyError,IntegrityError

from app.extensions import db
from app.models import Customer,SalesOrder,User,AuditLog
from app.services.customer_service import normalize_phone,save_customer,set_active,purchase_history,customer_query,DuplicateCustomer
from app.services.inventory_service import InventoryError
from test_auth import account,auth_client,csrf,login
from test_inventory import receipt,lines,create_document,transition,stock
from test_transactions import create_form,post_action


def profile(**changes):
    data=dict(name='Khách demo '+secrets.token_hex(4),phone='09'+''.join(str(secrets.randbelow(10)) for _ in range(8)),
              email='demo@example.invalid',address='Địa chỉ kiểm thử')
    data.update(changes)
    return data


def customer(account,**changes):
    db.session.rollback()
    return save_customer(account['id'],profile(**changes))


def sale(account,catalog,identifier=None,mode='existing',**changes):
    header=dict(customer_mode=mode,customer_id=identifier,customer_name='Tên giả mạo bị bỏ qua',
                customer_phone='0900000000',customer_email='walkin@example.invalid',customer_address='Snapshot')
    header.update(changes)
    return create_document('sales',account['id'],header,lines(catalog,1))


@pytest.mark.parametrize('value',['0901234567','090 123 4567','+84 (90) 123-4567','84901234567','+84901234567'])
def test_phone_equivalent(value):
    assert normalize_phone(value)=='+84901234567'


@pytest.mark.parametrize('value',['','abc','+840901234567','09012','+12025550123','０９０１２３４５６７','090123456789','00 901234567'])
def test_invalid_phone(value):
    with pytest.raises(InventoryError):normalize_phone(value)


def test_phone_uniqueness_inactive_and_no_name_merge(account):
    data=profile();identifier=save_customer(account['id'],data)
    db.session.rollback();set_active(account['id'],identifier,False)
    with pytest.raises(DuplicateCustomer):save_customer(account['id'],dict(data,phone=normalize_phone(data['phone'])))
    another=save_customer(account['id'],profile(name=data['name']))
    assert identifier != another
    db.session.rollback();set_active(account['id'],identifier,True)
    save_customer(account['id'],profile(name='Cập nhật'),identifier)
    db.session.rollback();assert db.session.get(Customer,identifier).is_active


def test_snapshot_and_multiple_orders(account,catalog):
    identifier=customer(account,name='Khách ban đầu')
    receipt(account,catalog,10,True)
    first=sale(account,catalog,identifier);second=sale(account,catalog,identifier)
    db.session.rollback();before=db.session.get(SalesOrder,first)
    old=(before.customer_name,before.customer_phone,before.customer_email,before.customer_address)
    save_customer(account['id'],profile(name='Khách đổi tên'),identifier)
    third=sale(account,catalog,identifier)
    db.session.rollback()
    order=db.session.get(SalesOrder,first)
    assert (order.customer_name,order.customer_phone,order.customer_email,order.customer_address)==old
    assert db.session.get(SalesOrder,second).customer_name=='Khách ban đầu'
    assert db.session.get(SalesOrder,third).customer_name=='Khách đổi tên'
    assert len(db.session.get(Customer,identifier).orders)==3


def test_history_completed_only_and_cancellation(account,catalog):
    identifier=customer(account);receipt(account,catalog,10,True)
    ids=[sale(account,catalog,identifier) for _ in range(3)]
    transition('sales',account['id'],ids[0],'complete')
    transition('sales',account['id'],ids[1],'cancel')
    db.session.rollback();actor=db.session.get(User,account['id'])
    history=purchase_history(identifier,actor)
    assert history['count']==1 and history['total']==Decimal('2345.67') and history['last'] is not None
    assert history['order_count']==3 and history['products'][0]['quantity']==1
    assert history['items'][ids[0]][0]['unit_price']==Decimal('2345.67')
    transition('sales',account['id'],ids[0],'cancel')
    db.session.rollback();history=purchase_history(identifier,actor)
    assert history['count']==0 and history['total']==0 and history['last'] is None and not history['products']


def test_walkin_never_links_by_phone(account,catalog):
    identifier=customer(account);receipt(account,catalog,5,True)
    db.session.rollback();phone=db.session.get(Customer,identifier).phone
    order=sale(account,catalog,identifier,mode='walkin',customer_phone=phone)
    db.session.rollback();assert db.session.get(SalesOrder,order).customer_id is None
    set_active(account['id'],identifier,False)
    with pytest.raises(InventoryError):sale(account,catalog,identifier)


def test_new_customer_order_atomic_and_duplicate(account,catalog):
    receipt(account,catalog,5,True);data=profile()
    header={('customer_'+key if key!='name' else 'customer_name'):value for key,value in data.items()}
    identifier=sale(account,catalog,mode='new',**header)
    db.session.rollback();record=db.session.get(SalesOrder,identifier)
    assert record.customer_id and record.customer_phone==normalize_phone(data['phone'])
    with pytest.raises(DuplicateCustomer):sale(account,catalog,mode='new',**header)
    failed=profile()
    with pytest.raises(InventoryError):
        create_document('sales',account['id'],dict(customer_mode='new',customer_name=failed['name'],customer_phone=failed['phone']),lines(catalog,100))
    db.session.rollback()
    assert db.session.scalar(select(Customer.id).where(Customer.phone==normalize_phone(failed['phone']))) is None


def test_injected_failure_rolls_back_customer_order_and_audit(account,catalog,monkeypatch):
    import app.services.transaction_service as service
    receipt(account,catalog,5,True);data=profile()
    before=db.session.scalar(select(func.count()).select_from(AuditLog))
    def fail(session,*args):
        session.flush();raise SQLAlchemyError('injected')
    monkeypatch.setattr(service,'audit',fail)
    with pytest.raises(InventoryError):sale(account,catalog,mode='new',customer_name=data['name'],customer_phone=data['phone'])
    db.session.rollback()
    assert db.session.scalar(select(Customer.id).where(Customer.phone==normalize_phone(data['phone']))) is None
    assert db.session.scalar(select(func.count()).select_from(AuditLog))==before
    assert stock(catalog)==5


def test_duplicate_concurrent_customers(mysql_app,account):
    data=profile();db.session.remove();barrier=Barrier(2)
    def worker(_):
        with mysql_app.app_context():
            barrier.wait(timeout=10)
            try:save_customer(account['id'],data);return 'ok'
            except DuplicateCustomer:return 'duplicate'
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(worker,range(2)))==['duplicate','ok']
    db.session.rollback()
    assert db.session.scalar(select(func.count()).select_from(Customer).where(Customer.phone==normalize_phone(data['phone'])))==1


def test_concurrent_inline_customer_order(mysql_app,account,catalog):
    receipt(account,catalog,5,True);data=profile();db.session.remove();barrier=Barrier(2)
    def worker(_):
        with mysql_app.app_context():
            barrier.wait(timeout=10)
            try:
                sale(account,catalog,mode='new',customer_name=data['name'],customer_phone=data['phone'])
                return 'ok'
            except DuplicateCustomer:return 'duplicate'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(worker,range(2)))==['duplicate','ok']
    db.session.rollback()
    identifier=db.session.scalar(select(Customer.id).where(Customer.phone==normalize_phone(data['phone'])))
    assert identifier and db.session.scalar(select(func.count()).select_from(SalesOrder).where(SalesOrder.customer_id==identifier))==1
    assert stock(catalog)==5


def test_duplicate_order_ticket_rolls_back_extra_customer(account,catalog):
    receipt(account,catalog,5,True);code='SO-CUSTOMER-'+catalog['suffix']
    first,second=profile(),profile()
    for index,data in enumerate([first,second]):
        header=dict(customer_mode='new',customer_name=data['name'],customer_phone=data['phone'])
        if index:
            with pytest.raises(InventoryError):create_document('sales',account['id'],header,lines(catalog,1),code)
        else:create_document('sales',account['id'],header,lines(catalog,1),code)
    db.session.rollback()
    assert db.session.scalar(select(Customer.id).where(Customer.phone==normalize_phone(second['phone']))) is None
    assert db.session.scalar(select(func.count()).select_from(SalesOrder).where(SalesOrder.order_code==code))==1


def test_staff_consulting_does_not_grant_order_access(auth_client,account,catalog):
    identifier=customer(account);receipt(account,catalog,10,True)
    completed=sale(account,catalog,identifier);draft=sale(account,catalog,identifier)
    transition('sales',account['id'],completed,'complete')
    db.session.rollback();db.session.get(SalesOrder,completed).notes='INTERNAL-SECRET';db.session.commit()
    admin=db.session.get(User,account['id']);admin.role='staff';db.session.commit()
    # Order owner is a different staff member from the current viewer.
    owner=db.session.get(User,catalog['user_id'])
    for oid in [completed,draft]:db.session.get(SalesOrder,oid).created_by=owner.id
    db.session.commit();login(auth_client,account)
    page=auth_client.get(f'/business/customers/{identifier}')
    assert page.status_code==200 and 'INTERNAL-SECRET' not in page.text
    assert f'data-customer-order="{completed}"' in page.text and f'data-customer-order="{draft}"' not in page.text
    assert f'href="/business/sales/{completed}"' not in page.text
    assert auth_client.get(f'/business/sales/{completed}').status_code==404
    assert post_action(auth_client,f'/business/sales/{completed}/cancel').status_code==404
    assert auth_client.get('/business/customers/new').status_code==403
    assert auth_client.get(f'/business/customers/{identifier}/edit').status_code==403
    assert post_action(auth_client,f'/business/customers/{identifier}/deactivate').status_code==403
    with pytest.raises(InventoryError):save_customer(account['id'],profile())
    with pytest.raises(InventoryError):set_active(account['id'],identifier,False)
    data=create_form(auth_client,'sales',catalog,customer_mode='new',customer_name='Khách Staff',customer_phone=profile()['phone'])
    assert auth_client.post('/business/sales/new',data=data).status_code==303


def test_search_admin_forms_csrf_and_audit(auth_client,account):
    data=profile();identifier=save_customer(account['id'],data)
    login(auth_client,account)
    for query in [data['name'],data['phone'],normalize_phone(data['phone']),data['email']]:
        response=auth_client.get('/business/customers',query_string={'q':query})
        assert response.status_code==200 and data['name'] in response.text
    assert any(c['id']==identifier for c in auth_client.get('/business/customers/search',query_string={'q':data['phone']}).json)
    assert auth_client.post('/business/customers/new',data=data).status_code==400
    duplicate=auth_client.post('/business/customers/new',data=dict(data,csrf_token=csrf(auth_client)))
    assert duplicate.status_code==409 and f'/business/customers/{identifier}' in duplicate.text
    assert auth_client.post('/business/customers/new',data=dict(data,phone='invalid',csrf_token=csrf(auth_client))).status_code==422
    assert post_action(auth_client,f'/business/customers/{identifier}/deactivate').status_code==303
    assert not auth_client.get('/business/customers/search',query_string={'q':data['phone']}).json
    db.session.rollback()
    audits=db.session.scalars(select(AuditLog).where(AuditLog.entity_type=='customers',AuditLog.entity_id==identifier)).all()
    assert [a.action for a in audits]==['create','deactivate']
    assert all(data['phone'] not in (a.description or '') and data['name'] not in (a.description or '') for a in audits)


@pytest.mark.parametrize('path',['/business/customers','/business/customers/search','/business/customers/new'])
def test_customer_anonymous(auth_client,path):
    assert auth_client.get(path).status_code==302


def test_empty_history_and_pagination(account,catalog):
    identifier=customer(account);db.session.rollback();actor=db.session.get(User,account['id'])
    empty=purchase_history(identifier,actor)
    assert empty['count']==0 and empty['total']==0 and not empty['rows'] and not empty['products']
    receipt(account,catalog,20,True)
    ids=[sale(account,catalog,identifier) for _ in range(11)]
    db.session.rollback();first=purchase_history(identifier,actor);second=purchase_history(identifier,actor,2)
    assert first['order_count']==11 and len(first['rows'])==10 and len(second['rows'])==1
    assert {r['id'] for r in first['rows']}|{r['id'] for r in second['rows']}==set(ids)


def test_update_duplicate_phone_and_rollback(account,monkeypatch):
    import app.services.customer_service as service
    a,b=customer(account),customer(account)
    db.session.rollback();original=db.session.get(Customer,a).phone;other=db.session.get(Customer,b).phone
    with pytest.raises(DuplicateCustomer):save_customer(account['id'],profile(phone=other),a)
    db.session.rollback();assert db.session.get(Customer,a).phone==original
    def fail(session,*args):session.flush();raise SQLAlchemyError('injected')
    monkeypatch.setattr(service,'customer_audit',fail)
    with pytest.raises(InventoryError):save_customer(account['id'],profile(name='Must roll back'),a)
    db.session.rollback();assert db.session.get(Customer,a).phone==original
    with pytest.raises(InventoryError):set_active(account['id'],a,False)
    db.session.rollback();assert db.session.get(Customer,a).is_active


def test_http_existing_snapshot_read_again_and_inactive(auth_client,account,catalog):
    identifier=customer(account);receipt(account,catalog,5,True);login(auth_client,account)
    data=create_form(auth_client,'sales',catalog,customer_mode='existing',customer_id=str(identifier),customer_name='Forged')
    new=profile(name='Current database profile');save_customer(account['id'],new,identifier)
    response=auth_client.post('/business/sales/new',data=data)
    assert response.status_code==303
    db.session.rollback();record=db.session.get(SalesOrder,int(response.location.rsplit('/',1)[1]))
    assert record.customer_name==new['name'] and record.customer_phone==normalize_phone(new['phone'])
    set_active(account['id'],identifier,False)
    data=create_form(auth_client,'sales',catalog,customer_mode='existing',customer_id=str(identifier))
    assert auth_client.post('/business/sales/new',data=data).status_code==422


@pytest.mark.parametrize('query',['page=0','product_page=bad','status=bad','q='+'x'*121])
def test_bad_list_queries(auth_client,account,query):
    login(auth_client,account)
    path='/business/customers'
    if query.startswith('product_page'):
        identifier=customer(account);path+=f'/{identifier}'
    assert auth_client.get(path+'?'+query).status_code==400
