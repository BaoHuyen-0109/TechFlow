"""Customer acceptance in Chromium; all fixtures guarded to db-test only."""
import json
import secrets
import time
import re
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
from verify_catalog_ui import ROOT,BASE,provision,capture
from verify_dashboard_ui import test_database
from verify_inventory_ui import confirm


def phone():return '09'+''.join(str(secrets.randbelow(10)) for _ in range(8))


def main():
    accounts,password=provision()
    errors=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        for role in ['admin','staff']:
            for viewport,width,height in [('desktop',1440,1000),('tablet',834,1112),('mobile',390,844)]:
                tag='UI51-'+secrets.token_hex(5).upper();number=phone()
                fixture=json.loads(test_database(f'''
from app.models import Customer,Business,User,SalesOrder
from app.services.customer_service import save_customer
from app.services.transaction_service import create_document,transition
admin=db.session.scalar(db.select(User.id).where(User.username=={accounts['admin']!r}))
staff=db.session.scalar(db.select(User.id).where(User.username=={accounts['staff']!r}))
category=Category(code={tag!r},name='Thiết bị tư vấn '+{tag!r})
supplier=Business(code={tag!r},name='Nhà cung cấp test khách hàng')
db.session.add_all([category,supplier]);db.session.flush()
product=Product(sku={tag!r},name='Laptop Dell demo và phụ kiện',category_id=category.id,business_id=supplier.id,purchase_price=Decimal('1234.56'),selling_price=Decimal('2345.67'),stock_quantity=0)
db.session.add(product);db.session.commit()
cid=save_customer(admin,dict(name='Khách demo '+{tag!r},phone={number!r},email='demo@example.invalid',address='Địa chỉ giả lập kiểm thử'))
incoming=create_document('purchases',admin,dict(business_id=supplier.id),[dict(product_id=product.id,quantity=10,unit_cost='1234.56')])
transition('purchases',admin,incoming,'complete')
sales=[]
for state in ['completed','draft','cancelled']:
    oid=create_document('sales',admin,dict(customer_mode='existing',customer_id=cid),[dict(product_id=product.id,quantity=1)])
    if state!='draft':transition('sales',admin,oid,'complete' if state=='completed' else 'cancel')
    sales.append(oid)
db.session.rollback();db.session.get(SalesOrder,sales[0]).notes='INTERNAL-CUSTOMER-PRIVATE';db.session.commit()
print(json.dumps(dict(customer=cid,product=product.id,orders=sales)))
'''))
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(BASE+'/login');page.locator('#identity').fill(accounts[role]);page.locator('#password').fill(password)
                page.get_by_role('button',name='Đăng nhập',exact=True).click();page.wait_for_url('**/'+role+'/dashboard')
                def shot(name):
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),name
                    capture(page,path=str(ROOT/'docs/screenshots'/f'stage51-{role}-{viewport}-{name}.png'),full_page=True)
                page.goto(BASE+'/business/customers');page.locator('#q').fill(number)
                with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Áp dụng',exact=True).click(no_wait_after=True)
                expect(page.locator('tbody tr')).to_have_count(1);shot('list')
                page.get_by_role('link',name='Xem lịch sử',exact=True).click();page.wait_for_url('**/customers/'+str(fixture['customer']))
                expect(page.locator('[data-customer-count]')).to_have_text('1');expect(page.locator('[data-customer-spent]')).to_have_text('2.345,67 ₫')
                assert 'INTERNAL-CUSTOMER-PRIVATE' not in page.locator('body').inner_text()
                assert page.locator('[data-customer-order]').count()==(3 if role=='admin' else 1)
                if role=='staff':
                    assert not page.locator(f'a[href="/business/sales/{fixture["orders"][0]}"]').count()
                    assert page.request.get(BASE+f'/business/sales/{fixture["orders"][0]}').status==404
                    assert page.request.get(BASE+f'/business/customers/{fixture["customer"]}/edit').status==403
                shot('profile')
                page.get_by_role('link',name='Lập đơn cho khách',exact=True).click();page.wait_for_url('**/sales/new?customer_id=*')
                expect(page.locator('#customer_name')).to_have_value('Khách demo '+tag)
                page.locator('#customer-search').fill(number)
                expect(page.locator('[data-customer-results] button')).to_have_count(1)
                page.locator('[data-customer-results] button').click()
                expect(page.locator('[data-customer-history]')).to_be_visible()
                page.locator('[data-product-search]').fill(tag)
                expect(page.locator('[data-search-status]')).to_contain_text('1 lựa chọn')
                page.locator('#lines-0-product_id').select_option(str(fixture['product']))
                page.locator('#lines-0-quantity').fill('1');shot('order-picker')
                with page.expect_response(lambda r:r.request.method=='POST' and urlsplit(r.url).path.endswith('/sales/new')) as response:
                    page.get_by_role('button',name='Lưu bản nháp',exact=True).click()
                assert response.value.status==303;page.wait_for_url(re.compile(r'/business/sales/\d+$'))
                created=int(page.url.rsplit('/',1)[1]);confirm(page,'Xác nhận hoàn thành','complete')
                page.goto(BASE+'/business/customers/'+str(fixture['customer']))
                expect(page.locator('[data-customer-count]')).to_have_text('2');expect(page.locator('[data-customer-spent]')).to_have_text('4.691,34 ₫')
                shot('profile-after-sale')
                # Inline creation and duplicate rejection, then deliberate walk-in.
                newphone=phone();page.goto(BASE+'/business/sales/new')
                page.locator('#customer_mode').select_option('new');page.locator('#customer_name').fill('Khách mới '+tag);page.locator('#customer_phone').fill(newphone)
                page.locator('[data-product-search]').fill(tag);expect(page.locator('[data-search-status]')).to_contain_text('1 lựa chọn')
                page.locator('#lines-0-product_id').select_option(str(fixture['product']))
                with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Lưu bản nháp',exact=True).click(no_wait_after=True)
                assert '/sales/new' not in page.url
                page.goto(BASE+'/business/sales/new');page.locator('#customer_mode').select_option('new')
                page.locator('#customer_name').fill('Khách trùng số');page.locator('#customer_phone').fill(newphone)
                page.locator('[data-product-search]').fill(tag);expect(page.locator('[data-search-status]')).to_contain_text('1 lựa chọn')
                page.locator('#lines-0-product_id').select_option(str(fixture['product']))
                with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/sales/new')) as response:
                    page.get_by_role('button',name='Lưu bản nháp',exact=True).click()
                assert response.value.status==409;expect(page.get_by_role('alert').filter(has_text='Số điện thoại đã có hồ sơ')).to_be_visible()
                page.locator('#customer_mode').select_option('walkin')
                with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Lưu bản nháp',exact=True).click(no_wait_after=True)
                walkin=int(page.url.rsplit('/',1)[1])
                test_database(f'from app.models import SalesOrder\nassert db.session.get(SalesOrder,{walkin}).customer_id is None')
                if role=='admin':
                    page.goto(BASE+f'/business/customers/{fixture["customer"]}/edit')
                    page.locator('#name').fill('Hồ sơ cập nhật '+tag);page.locator('#phone').fill(phone());shot('edit')
                    with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Lưu hồ sơ',exact=True).click(no_wait_after=True)
                    test_database(f'from app.models import SalesOrder\nassert db.session.get(SalesOrder,{created}).customer_name=='+repr('Khách demo '+tag))
                    page.locator('input[type=checkbox]').check()
                    with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Vô hiệu hóa',exact=True).click(no_wait_after=True)
                    expect(page.get_by_role('button',name='Kích hoạt lại',exact=True)).to_be_visible()
                print(f'Customers {role} {viewport}: lookup, history, snapshot, inline create, duplicate and walk-in passed.',flush=True)
                context.close()
                time.sleep(7)  # Respect the real proxy login limiter, never disable it.
        browser.close()
    assert not errors,errors
    print('Customer UI passed: 6 role/viewport flows. Screenshots local; demo untouched.',flush=True)


if __name__=='__main__':main()
