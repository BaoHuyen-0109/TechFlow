"""UI acceptance on port 8001 only; all fixtures are guarded db-test data."""
import json
import secrets
import time

from playwright.sync_api import sync_playwright, expect
from verify_catalog_ui import ROOT, BASE, provision
from verify_dashboard_ui import test_database


def check_progress(page, status, expected):
    panel = page.locator('[data-progress-status]')
    expect(panel).to_have_attribute('data-progress-status', status)
    assert panel.locator('[data-stage]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.stage)') == expected
    expect(panel.locator('[aria-current="step"]')).to_have_count(1)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')


def screenshot(page, name):
    # Evidence annotation is allowed exclusively after both URL and DB guards.
    assert page.url.startswith(BASE + '/')
    assert json.loads(test_database("print(json.dumps(app.config['APP_ENV']))")) == 'testing'
    page.locator('.ws-content').evaluate("main=>main.insertAdjacentHTML('afterbegin','<p class=wr-notice>DỮ LIỆU KIỂM THỬ RIÊNG — KHÔNG PHẢI DATABASE DEMO</p>')")
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.screenshot(path=str(ROOT/'docs/screenshots'/('prestage7-'+name+'.png')), full_page=True)


def check_copy_code(page):
    url = page.url
    code = page.locator('#document-code').inner_text()
    button = page.get_by_role('button', name='Sao chép mã giao dịch', exact=True)
    expect(button).to_be_visible()
    button.focus(); page.keyboard.press('Enter')
    expect(page.locator('[data-copy-feedback]')).to_have_text('Đã sao chép mã giao dịch.')
    assert page.evaluate('navigator.clipboard.readText()') == code
    assert page.url == url
    expect(button).to_be_focused()
    # Clipboard denial must offer manual copy, without navigation or pageerror.
    page.evaluate("window.detailWriteText=navigator.clipboard.writeText; Object.defineProperty(navigator.clipboard,'writeText',{configurable:true,value:()=>Promise.reject(new DOMException('Blocked','NotAllowedError'))})")
    button.click()
    expect(page.locator('[data-copy-feedback]')).to_contain_text('Mã đã được chọn')
    assert page.evaluate('window.getSelection().toString()') == code
    expect(button).to_be_enabled()
    page.evaluate("Object.defineProperty(navigator.clipboard,'writeText',{configurable:true,value:window.detailWriteText}); window.getSelection().removeAllRanges()")
    button.click()
    expect(page.locator('[data-copy-feedback]')).to_have_text('Đã sao chép mã giao dịch.')
    assert page.url == url
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')


def main():
    accounts, password = provision()
    errors, assets = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for role in ['admin', 'staff']:
            for viewport, width, height in [('desktop',1440,1000),('tablet',834,1112),('mobile',390,844)]:
                tag = 'DETAIL-'+secrets.token_hex(5).upper()
                phone = '09'+str(int(secrets.token_hex(5),16))[-8:]
                data = json.loads(test_database(f'''
from app.models import Business,User,SalesOrder,SalesOrderItem,WarrantyCoverage
from app.services.transaction_service import create_document,transition
from app.services.customer_service import save_customer
from app.services.warranty_service import create_ticket,handle_ticket,local_day
admin=db.session.scalar(db.select(User.id).where(User.username=={accounts['admin']!r}))
staff=db.session.scalar(db.select(User.id).where(User.username=={accounts['staff']!r}))
actor=admin if {role!r}=='admin' else staff
category=Category(code={tag!r},name='Thiết bị tinh chỉnh '+{tag!r});supplier=Business(code={tag!r},name='Nhà cung cấp kiểm thử',contact_person='Liên hệ giả lập',phone='0901234567')
db.session.add_all([category,supplier]);db.session.flush()
product=Product(sku={tag!r},name='Thiết bị công nghệ và máy lọc nước kiểm thử',category_id=category.id,business_id=supplier.id,purchase_price=Decimal('1234.56'),selling_price=Decimal('2345.67'),warranty_enabled=True,warranty_months=12,warranty_notes='Kiểm tra lỗi thực tế; còn hạn không tự động miễn phí.')
db.session.add(product);db.session.commit()
incoming=create_document('purchases',admin,dict(business_id=supplier.id),[dict(product_id=product.id,quantity=40,unit_cost='1234.56')]);transition('purchases',admin,incoming,'complete')
draft_in=create_document('purchases',admin,dict(business_id=supplier.id),[dict(product_id=product.id,quantity=2,unit_cost='1234.56')])
cid=save_customer(admin,dict(name='Khách hồ sơ '+{tag!r},phone={phone!r},email='demo@example.invalid',address='Địa chỉ kiểm thử'))
header=dict(customer_mode='existing',customer_id=cid)
def sale(owner=actor):
    return create_document('sales',owner,header,[dict(product_id=product.id,quantity=1)])
draft=sale();cancelled_draft=sale();transition('sales',actor,cancelled_draft,'cancel')
cancelled_completed=sale();transition('sales',actor,cancelled_completed,'complete');transition('sales',admin,cancelled_completed,'cancel')
other=create_document('sales',admin,header,[dict(product_id=product.id,quantity=8)]);transition('sales',admin,other,'complete')
db.session.rollback();item=db.session.scalar(db.select(SalesOrderItem).where(SalesOrderItem.order_id==other))
tickets={{}}
for unit,target in enumerate(['received','processing','completed','returned','rejected','returned-rejected','returned-after-processing-rejection'],1):
    tid=create_ticket(actor,item.id,unit,{tag!r}+'-'+str(unit),'Máy không hoạt động, khách cần kiểm tra.')
    if target in ['processing','completed','returned','returned-after-processing-rejection']:
        handle_ticket(actor,tid,'processing','received',result='Đã đối chiếu thiết bị và điều kiện chính sách.')
    if target in ['completed','returned']:
        handle_ticket(actor,tid,'completed','processing',result='Đã xử lý lỗi kỹ thuật.')
    if target in ['rejected','returned-rejected','returned-after-processing-rejection']:
        handle_ticket(actor,tid,'rejected','processing' if target=='returned-after-processing-rejection' else 'received',result='Kiểm tra có hư hỏng ngoại lực.',reason='Không thuộc điều kiện bảo hành dù còn hạn.')
    if target in ['returned','returned-rejected','returned-after-processing-rejection']:
        handle_ticket(actor,tid,'returned','completed' if target=='returned' else 'rejected')
    tickets[target]=tid
policy_items={{}}
for mode in ['expired','off','unknown']:
    db.session.rollback();product=db.session.get(Product,product.id)
    if mode=='off':product.warranty_enabled=False;product.warranty_months=None;db.session.commit()
    if mode=='unknown':
        old=SalesOrder(order_code={tag!r}+'-OLD',customer_name='Khách đơn cũ',created_by=admin,order_date=datetime(2025,1,31),status='completed',total_amount=Decimal('2345.67'))
        db.session.add(old);db.session.flush();line=SalesOrderItem(order_id=old.id,product_id=product.id,quantity=1,unit_price=Decimal('2345.67'),line_total=Decimal('2345.67'));db.session.add(line);db.session.commit()
    else:
        oid=sale();transition('sales',actor,oid,'complete');db.session.rollback();line=db.session.scalar(db.select(SalesOrderItem).where(SalesOrderItem.order_id==oid))
        if mode=='expired':
            coverage=db.session.scalar(db.select(WarrantyCoverage).where(WarrantyCoverage.sale_item_id==line.id));coverage.starts_on=local_day()-timedelta(days=400);coverage.expires_on=local_day()-timedelta(days=1);db.session.commit()
    policy_items[mode]=line.id
print(json.dumps(dict(draft=draft,incoming=incoming,draft_in=draft_in,customer=cid,product=product.id,other=other,cancelled_draft=cancelled_draft,cancelled_completed=cancelled_completed,tickets=tickets,policy_items=policy_items)))
'''))
                context = browser.new_context(viewport={'width':width,'height':height}, reduced_motion='reduce', locale='vi-VN')
                context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE)
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('response', lambda response: assets.append(response.url) if '/static/' in response.url and response.status>=400 else None)
                page.goto(BASE+'/login');page.locator('#identity').fill(accounts[role]);page.locator('#password').fill(password)
                page.get_by_role('button',name='Đăng nhập',exact=True).click();page.wait_for_url('**/'+role+'/dashboard')
                sale_url=BASE+f'/business/sales/{data["draft"]}'
                page.goto(sale_url);check_progress(page,'draft',['draft','completed'])
                assert 'DỮ LIỆU KIỂM THỬ RIÊNG' not in page.content()
                check_copy_code(page)
                expect(page.locator('[data-document-total]')).to_have_text('2.345,67 ₫')
                assert page.request.post(sale_url+'/complete',data={}).status==400
                trigger=page.get_by_role('button',name='Xác nhận hoàn thành',exact=True)
                trigger.focus();page.keyboard.press('Enter');expect(page.locator('#transaction-confirm')).to_be_visible()
                expect(page.locator('#transaction-confirm')).to_be_focused()
                expect(page.locator('#transaction-confirm')).to_have_attribute('aria-describedby','confirm-message')
                page.keyboard.press('Escape');expect(page.locator('#transaction-confirm')).to_be_hidden();expect(trigger).to_be_focused()
                trigger.press('Enter');expect(page.locator('#confirm-message')).to_contain_text('giảm tồn kho')
                expect(page.locator('#transaction-confirm')).to_be_focused()
                # Observe loading during the real submit event. DOM access from a
                # paused navigation route deadlocks Chromium's old document.
                page.locator('[data-confirm-form]').evaluate("form=>form.addEventListener('submit',()=>sessionStorage.setItem('detail-loading',JSON.stringify(form.getAttribute('aria-busy')==='true' && form.querySelector('button').disabled)))")
                with page.expect_navigation(wait_until='domcontentloaded'):
                    page.get_by_role('button',name='Đồng ý thực hiện',exact=True).press('Enter',no_wait_after=True)
                assert page.evaluate("sessionStorage.getItem('detail-loading')")=='true'
                check_progress(page,'completed',['draft','completed'])
                if role=='staff':expect(page.get_by_role('button',name='Hủy giao dịch',exact=True)).to_have_count(0)
                if role=='staff' and viewport=='mobile':screenshot(page,'staff-mobile-sale')
                for key,expected in [('cancelled_draft',['draft','cancelled']),('cancelled_completed',['draft','completed','cancelled'])]:
                    page.goto(BASE+f'/business/sales/{data[key]}');check_progress(page,'cancelled',expected)
                    expect(page.get_by_role('button',name='Xác nhận hoàn thành',exact=True)).to_have_count(0)
                if role=='admin':
                    page.goto(BASE+f'/business/purchases/{data["incoming"]}');check_progress(page,'completed',['draft','completed'])
                    assert 'DỮ LIỆU KIỂM THỬ RIÊNG' not in page.content()
                    check_copy_code(page)
                    assert page.request.post(page.url+'/cancel',data={}).status==400
                    cancel=page.get_by_role('button',name='Hủy giao dịch',exact=True)
                    cancel.focus();page.keyboard.press('Enter')
                    expect(page.locator('#transaction-confirm')).to_be_focused()
                    expect(page.locator('#confirm-message')).to_contain_text('từng sản phẩm đủ')
                    expect(page.locator('#confirm-message')).to_contain_text('toàn bộ thao tác hủy bị từ chối')
                    page.keyboard.press('Escape');expect(page.locator('#transaction-confirm')).to_be_hidden();expect(cancel).to_be_focused()
                    if viewport=='desktop':
                        plain_context=browser.new_context(storage_state=context.storage_state(),java_script_enabled=False)
                        plain=plain_context.new_page();plain.goto(page.url)
                        expect(plain.locator('[data-copy-code]')).to_be_hidden()
                        expect(plain.locator('#document-code')).to_have_text(page.locator('#document-code').inner_text())
                        plain_context.close()
                    if viewport=='desktop':screenshot(page,'admin-desktop-purchase')
                    page.goto(BASE+f'/business/purchases/{data["draft_in"]}');check_progress(page,'draft',['draft','completed'])
                else:
                    assert page.request.get(BASE+f'/business/purchases/{data["incoming"]}').status==403
                    assert page.request.get(BASE+f'/business/sales/{data["other"]}').status==404
                for state,tid in data['tickets'].items():
                    page.goto(BASE+f'/business/warranties/{tid}')
                    rejected=state in ['rejected','returned-rejected','returned-after-processing-rejection']
                    expected=['received','processing','completed','returned'] if not rejected else ['received','processing','rejected','returned'] if state=='returned-after-processing-rejection' else ['received','rejected','returned']
                    check_progress(page,'returned' if state.startswith('returned') else state,expected)
                    expect(page.locator('[data-policy-state]')).to_have_attribute('data-policy-state','valid')
                    assert page.request.get(BASE+page.locator('[data-related-customer]').get_attribute('href')).status==200
                    assert page.request.get(BASE+page.locator('[data-related-product]').get_attribute('href')).status==200
                    expect(page.locator('[data-related-sale]')).to_have_count(1 if role=='admin' else 0)
                    if role=='admin':assert page.request.get(BASE+page.locator('[data-related-sale]').get_attribute('href')).status==200
                    if rejected:expect(page.locator('[data-assessment]')).to_have_text('Đã từ chối')
                    if state=='returned-rejected' and role=='admin' and viewport=='desktop':screenshot(page,'admin-desktop-warranty-rejected')
                    if state=='returned' and role=='staff' and viewport=='mobile':screenshot(page,'staff-mobile-warranty-returned')
                for mode,item in data['policy_items'].items():
                    page.goto(BASE+f'/business/warranties/new/{item}')
                    expect(page.locator('[data-policy-state]')).to_have_attribute('data-policy-state',mode)
                assert page.request.get(BASE+'/admin/dashboard').status==(200 if role=='admin' else 403)
                print(f'Detail polish {role} {viewport}: timelines, copy/fallback, branches, policy labels, links, CSRF, cancellation explanation, modal keyboard/loading and responsive passed.',flush=True)
                context.close();time.sleep(7)
        browser.close()
    assert not errors and not assets,errors+assets
    print('Detail UI acceptance passed: 6 role/viewport flows, 7 warranty states, 4 policy states; exactly 4 evidence screenshots.')


if __name__=='__main__':main()
