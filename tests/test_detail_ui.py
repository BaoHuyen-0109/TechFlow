"""Presentation must reflect real states and keep existing record access rules."""
from datetime import timedelta
from html.parser import HTMLParser

import pytest
from flask import render_template_string
from sqlalchemy import select, func

from app.extensions import db
from app.models import User, SalesOrder, PurchaseReceipt, AuditLog, WarrantyEvent, WarrantyCoverage
from app.services.warranty_service import coverage_state, local_day
from test_auth import account, auth_client, login
from test_inventory import receipt, lines, create_document, transition
from test_warranties import sold, intake, action


class ProgressParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.stages = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'li' and 'data-stage' in attrs:
            self.stages[attrs['data-stage']] = attrs


@pytest.mark.parametrize('kind', ['purchases', 'sales'])
@pytest.mark.parametrize('state', ['draft', 'completed', 'cancelled-draft', 'cancelled-completed'])
def test_transaction_progress_uses_actual_completion(auth_client, account, catalog, kind, state):
    receipt(account, catalog, 10, True)
    header = dict(business_id=catalog['business_id']) if kind == 'purchases' else dict(customer_name='Khách kiểm thử')
    oid = create_document(kind, account['id'], header, lines(catalog, 1))
    if state in {'completed', 'cancelled-completed'}:
        transition(kind, account['id'], oid, 'complete')
    if state.startswith('cancelled'):
        transition(kind, account['id'], oid, 'cancel')
    db.session.rollback()
    login(auth_client, account)
    page = auth_client.get(f'/business/{kind}/{oid}')
    assert page.status_code == 200
    stages = ProgressParser(page.text).stages
    current = 'cancelled' if state.startswith('cancelled') else state
    assert stages[current]['aria-current'] == 'step'
    if state == 'cancelled-draft':
        assert 'completed' not in stages  # No timestamp/evidence may be invented.
    if state == 'cancelled-completed':
        assert 'detail-step--done' in stages['completed']['class']
    assert 'data-document-total' in page.text and 'data-document-quantity' in page.text
    assert 'aria-describedby="confirm-message"' in page.text
    assert 'data-confirm-form' in page.text and 'name="csrf_token"' in page.text
    code = db.session.get(PurchaseReceipt if kind == 'purchases' else SalesOrder, oid)
    expected_code = code.receipt_code if kind == 'purchases' else code.order_code
    assert f'data-copy-code="{expected_code}"' in page.text
    if kind == 'purchases' and state == 'completed':
        assert 'Nếu bất kỳ sản phẩm nào thiếu tồn kho' in page.text
        assert 'phiếu và tồn kho giữ nguyên' in page.text


@pytest.mark.parametrize('state', ['received', 'processing', 'completed', 'returned', 'rejected', 'returned-rejected'])
def test_warranty_progress_preserves_events(auth_client, account, sold, state):
    tid = intake(sold)
    if state in {'processing', 'completed', 'returned'}:
        action(sold, tid, 'processing', 'received')
    if state in {'completed', 'returned'}:
        action(sold, tid, 'completed', 'processing')
    if state in {'rejected', 'returned-rejected'}:
        action(sold, tid, 'rejected', 'received', reason='Không thuộc điều kiện')
    if state in {'returned', 'returned-rejected'}:
        action(sold, tid, 'returned', 'completed' if state == 'returned' else 'rejected')
    db.session.rollback()
    before = db.session.scalar(select(func.count()).select_from(WarrantyEvent).where(WarrantyEvent.ticket_id == tid))
    login(auth_client, account)
    page = auth_client.get(f'/business/warranties/{tid}')
    assert page.status_code == 200
    stages = ProgressParser(page.text).stages
    assert stages['returned' if state == 'returned-rejected' else state]['aria-current'] == 'step'
    if state in {'rejected', 'returned-rejected'}:
        assert 'completed' not in stages and 'processing' not in stages
        assert 'rejected' in stages
    assert 'data-policy-state="valid"' in page.text and 'data-assessment' in page.text
    assert db.session.scalar(select(func.count()).select_from(WarrantyEvent).where(WarrantyEvent.ticket_id == tid)) == before


@pytest.mark.parametrize('role,owner', [('admin', False), ('staff', True), ('staff', False)])
def test_warranty_order_links_respect_existing_scope(auth_client, account, sold, role, owner):
    if not owner:
        other = User(username='other-'+account['username'], full_name='Người lập khác', role='admin')
        other.set_password(account['password'])
        db.session.add(other); db.session.flush()
        db.session.get(SalesOrder, sold['order']).created_by = other.id
    db.session.get(User, account['id']).role = role
    db.session.commit()
    tid = intake(sold)
    login(auth_client, account)
    page = auth_client.get(f'/business/warranties/{tid}')
    assert page.status_code == 200
    allowed = role == 'admin' or owner
    assert ('data-related-sale' in page.text) == allowed
    assert 'data-related-product' in page.text
    assert auth_client.get(f'/business/sales/{sold["order"]}').status_code == (200 if allowed else 404)
    assert auth_client.post(f'/business/warranties/{tid}/handle', data={'target':'processing'}).status_code == 400


@pytest.mark.parametrize('mode,expected', [('valid','valid'), ('expired','expired'), ('off','off'), ('unknown','unknown')])
def test_policy_labels_do_not_infer_unknown(mode, expected, mysql_app):
    coverage = None if mode == 'unknown' else WarrantyCoverage(enabled=mode != 'off', months=None if mode == 'off' else 12)
    if coverage and coverage.enabled:
        coverage.starts_on = local_day() - timedelta(days=400)
        coverage.expires_on = local_day() + timedelta(days=1 if mode == 'valid' else -1)
    with mysql_app.test_request_context():
        html = render_template_string("{% from 'warranties/macros.html' import policy %}{{ policy(coverage,coverage_state) }}", coverage=coverage, coverage_state=coverage_state)
    assert f'data-policy-state="{expected}"' in html
    assert coverage_state(coverage) in html


@pytest.mark.parametrize('kind', ['purchases', 'sales'])
@pytest.mark.parametrize('state', ['completed', 'cancelled'])
def test_legacy_without_operation_dates_does_not_invent_them(auth_client, account, catalog, kind, state):
    from datetime import datetime
    marker = 'legacy-'+catalog['suffix']
    if kind == 'sales':
        record = SalesOrder(order_code=marker, customer_name='Khách đơn cũ', created_by=account['id'], order_date=datetime(2020,1,1), status=state)
    else:
        record = PurchaseReceipt(receipt_code=marker, business_id=catalog['business_id'], created_by=account['id'], receipt_date=datetime(2020,1,1), status=state)
    record.created_at = datetime(2020,1,1)
    record.updated_at = datetime(2035,12,31)
    db.session.add(record);db.session.flush()
    # Same numeric ID for a different entity must not become this record's date.
    db.session.add(AuditLog(user_id=account['id'],action='complete',entity_type='unrelated_entity',entity_id=record.id,description='PRIVATE-AUDIT-NOT-FOR-UI'))
    db.session.commit()
    login(auth_client,account)
    page=auth_client.get(f'/business/{kind}/{record.id}')
    assert page.status_code==200
    stages=ProgressParser(page.text).stages
    if state=='cancelled':assert 'completed' not in stages
    assert '31/12/2035' not in page.text and 'PRIVATE-AUDIT-NOT-FOR-UI' not in page.text
    if state=='cancelled':assert 'Không ghi nhận mốc thời gian hủy' in page.text


@pytest.mark.parametrize('kind', ['purchases', 'sales'])
def test_operation_timestamps_in_same_minute_are_not_adjusted(auth_client, account, catalog, kind):
    from datetime import datetime
    receipt(account, catalog, 10, True)
    header = dict(business_id=catalog['business_id']) if kind == 'purchases' else dict(customer_name='Khách kiểm thử')
    oid = create_document(kind, account['id'], header, lines(catalog, 1))
    transition(kind, account['id'], oid, 'complete')
    transition(kind, account['id'], oid, 'cancel')
    db.session.rollback()
    model = PurchaseReceipt if kind == 'purchases' else SalesOrder
    record = db.session.get(model, oid)
    record.created_at = datetime(2024, 1, 15, 3, 19, 50)
    record.updated_at = datetime(2035, 12, 31)
    completed = datetime(2024, 1, 15, 3, 20, 10)
    cancelled = datetime(2024, 1, 15, 3, 20, 50)
    if kind == 'sales': record.completed_at = completed
    for entry in db.session.scalars(select(AuditLog).where(AuditLog.entity_type == model.__tablename__, AuditLog.entity_id == oid)):
        if entry.action == 'complete': entry.created_at = completed
        if entry.action == 'cancel': entry.created_at = cancelled
    db.session.commit()
    login(auth_client, account)
    page = auth_client.get(f'/business/{kind}/{oid}')
    assert page.status_code == 200
    timeline = page.text.split('data-progress-status=', 1)[1].split('</section>', 1)[0]
    assert timeline.count('10:20 · 15/01/2024') == 2
    assert '10:21' not in timeline and '2035' not in timeline


@pytest.mark.parametrize('environment', ['testing', 'development', 'production'])
@pytest.mark.parametrize('kind', ['purchases', 'sales'])
def test_screenshot_banner_is_never_rendered_by_application(auth_client, account, catalog, mysql_app, monkeypatch, environment, kind):
    receipt(account, catalog, 10, True)
    header = dict(business_id=catalog['business_id']) if kind == 'purchases' else dict(customer_name='Khách kiểm thử')
    oid = create_document(kind, account['id'], header, lines(catalog, 1))
    login(auth_client, account)
    monkeypatch.setitem(mysql_app.config, 'APP_ENV', environment)
    monkeypatch.setitem(mysql_app.config, 'TESTING', environment == 'testing')
    page = auth_client.get(f'/business/{kind}/{oid}')
    assert page.status_code == 200
    assert 'DỮ LIỆU KIỂM THỬ RIÊNG' not in page.text
    assert 'KHÔNG PHẢI DATABASE DEMO' not in page.text
