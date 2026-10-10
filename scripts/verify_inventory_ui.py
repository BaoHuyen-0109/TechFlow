"""Stage 5 acceptance. Hard guard: exclusively isolated Docker test application."""
import json
import secrets
import re

from playwright.sync_api import sync_playwright, expect
from verify_catalog_ui import ROOT, BASE, provision, capture
from verify_dashboard_ui import test_database


def check_stock(ids, expected):
    test_database(f"""
db.session.rollback()
assert [db.session.get(Product, identifier).stock_quantity for identifier in {ids!r}] == {expected!r}
""")


def confirm(page, label, action, status=303):
    page.get_by_role('button',name=label,exact=True).click()
    expect(page.locator('#transaction-confirm')).to_be_visible()
    with page.expect_response(lambda response: response.request.method=='POST' and response.url.endswith('/'+action)) as result:
        page.get_by_role('button',name='Đồng ý thực hiện',exact=True).click()
    assert result.value.status==status
    page.wait_for_load_state()


def main():
    accounts,password=provision()
    errors,assets=[],[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        for role in ['admin','staff']:
            for viewport,width,height in [('desktop',1440,1000),('tablet',834,1112),('mobile',390,844)]:
                tag='UI5-'+secrets.token_hex(5).upper()
                payload=json.loads(test_database(f"""
from app.models import Business, User
category=Category(code={tag!r},name='Thiết bị giao dịch '+{tag!r})
supplier=Business(code={tag!r},name='Nhà cung cấp demo kiểm thử')
db.session.add_all([category,supplier]);db.session.flush()
products=[]
for index in range(2):
    product=Product(sku={tag!r}+'-'+str(index),name='SSD NVMe kiểm thử '+str(index),category_id=category.id,business_id=supplier.id,purchase_price=Decimal('1234.56'),selling_price=Decimal('2345.67'),stock_quantity=0,reorder_level=1)
    db.session.add(product);products.append(product)
db.session.commit()
print(json.dumps(dict(products=[p.id for p in products],business=supplier.id,admin=db.session.scalar(db.select(User.id).where(User.username=={accounts['admin']!r})),staff=db.session.scalar(db.select(User.id).where(User.username=={accounts['staff']!r})))))
"""))
                ids=payload['products']
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                page=context.new_page()
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('response',lambda response:assets.append(response.url) if '/static/' in response.url and response.status>=400 else None)
                page.goto(BASE+'/login');page.locator('#identity').fill(accounts[role]);page.locator('#password').fill(password)
                page.get_by_role('button',name='Đăng nhập',exact=True).click();page.wait_for_url('**/'+role+'/dashboard')
                def shot(name):
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'),name+' horizontal overflow'
                    capture(page,path=str(ROOT/'docs/screenshots'/f'stage5-{role}-{viewport}-{name}.png'),full_page=True)
                def select_products(kind):
                    page.goto(BASE+'/business/'+kind+'/new')
                    page.locator('[data-product-search]').fill(tag)
                    expect(page.locator('[data-search-status]')).to_contain_text('2 lựa chọn')
                    page.locator('#lines-0-product_id').select_option(str(ids[0]))
                if role=='admin':
                    select_products('purchases')
                    page.locator('#business_id').select_option(str(payload['business']))
                    page.locator('#lines-0-quantity').fill('5');page.locator('#lines-0-unit_cost').fill('1234.56')
                    page.get_by_role('button',name='Thêm dòng sản phẩm',exact=True).click()
                    page.locator('#lines-1-product_id').select_option(str(ids[1]));page.locator('#lines-1-quantity').fill('3');page.locator('#lines-1-unit_cost').fill('0.01')
                    # Removing/re-adding preserves unique FieldList names.
                    page.locator('[data-remove]').last.click();page.get_by_role('button',name='Thêm dòng sản phẩm',exact=True).click()
                    page.locator('[data-product]').last.select_option(str(ids[1]));page.locator('[data-quantity]').last.fill('3');page.locator('[data-cost]').last.fill('0.01')
                    expect(page.locator('[data-grand-total]')).to_have_text('6.172,83 ₫')
                    shot('purchase-form')
                    page.get_by_role('button',name='Lưu bản nháp',exact=True).click();page.wait_for_url('**/business/purchases/*')
                    receipt_url=page.url;receipt_id=int(receipt_url.rsplit('/',1)[1])
                    expect(page.locator('[data-document-total]')).to_have_text('6.172,83 ₫');check_stock(ids,[0,0])
                    confirm(page,'Xác nhận hoàn thành','complete');check_stock(ids,[5,3]);shot('purchase-completed')
                else:
                    receipt_id=json.loads(test_database(f"""
from app.services.purchase_service import create_receipt, complete_receipt
identifier=create_receipt({payload['admin']},dict(business_id={payload['business']}),[dict(product_id={ids[0]},quantity=5,unit_cost='1234.56'),dict(product_id={ids[1]},quantity=3,unit_cost='0.01')])
complete_receipt({payload['admin']},identifier)
print(json.dumps(identifier))
"""))
                    receipt_url=BASE+'/business/purchases/'+str(receipt_id)
                    assert page.goto(BASE+'/business/purchases').status==403
                    assert page.goto(BASE+'/admin/dashboard').status==403
                    shot('admin-forbidden')
                select_products('sales')
                page.locator('#customer_name').fill('Khách hàng kiểm thử')
                page.locator('#customer_phone').fill('0901234567')
                page.locator('#lines-0-quantity').fill('2')
                expect(page.locator('[data-price]')).to_have_text('2.345,67 ₫')
                expect(page.locator('[data-stock]')).to_contain_text('5')
                shot('sales-form')
                page.get_by_role('button',name='Lưu bản nháp',exact=True).click();page.wait_for_url('**/business/sales/*')
                sale_url=page.url;sale_id=int(sale_url.rsplit('/',1)[1])
                expect(page.locator('[data-document-total]')).to_have_text('4.691,34 ₫');check_stock(ids,[5,3])
                confirm(page,'Xác nhận hoàn thành','complete');check_stock(ids,[3,3]);shot('sales-completed')
                if role=='admin':
                    page.goto(receipt_url);confirm(page,'Hủy giao dịch','cancel',409)
                    expect(page.locator('[role=alert]')).to_contain_text('không đủ tồn kho');check_stock(ids,[3,3])
                    page.goto(sale_url);confirm(page,'Hủy giao dịch','cancel');check_stock(ids,[5,3])
                    page.goto(receipt_url);confirm(page,'Hủy giao dịch','cancel');check_stock(ids,[0,0])
                else:
                    assert page.get_by_role('button',name='Hủy giao dịch',exact=True).count()==0
                    test_database(f"""
from app.services.sales_service import cancel_order
cancel_order({payload['admin']},{sale_id})
""")
                    check_stock(ids,[5,3])
                    page.goto(sale_url);expect(page.locator('h1')).to_contain_text('SO-')
                    # The same Staff may cancel their own draft, without a stock change.
                    select_products('sales');page.locator('#customer_name').fill('Đơn nháp cần hủy');page.locator('#lines-0-quantity').fill('1')
                    page.get_by_role('button',name='Lưu bản nháp',exact=True).click();page.wait_for_url('**/business/sales/*')
                    confirm(page,'Hủy giao dịch','cancel');check_stock(ids,[5,3])
                page.goto(BASE+'/business/sales?status=cancelled');shot('sales-list')
                page.goto(BASE+'/business/inventory?q='+tag);expect(page.locator('tbody tr').first).to_contain_text(tag);shot('movements')
                page.goto(BASE+'/staff/dashboard');expect(page.locator('[data-kpi=products]')).to_be_visible()
                state=context.storage_state()
                if viewport=='desktop' and role=='admin':
                    no_js=browser.new_context(storage_state=state,java_script_enabled=False)
                    simple=no_js.new_page();simple.goto(BASE+'/business/purchases/new')
                    expect(simple.locator('[data-add-line]')).to_be_hidden()
                    expect(simple.locator('[data-remove]')).to_be_hidden()
                    expect(simple.locator('[data-product-search]')).to_be_hidden()
                    simple.locator('#business_id').select_option(str(payload['business']))
                    # New fixture may be beyond the initial 50 choices: direct valid ID
                    # is covered by HTTP tests; use an available option for no-JS UI.
                    option=simple.locator('#lines-0-product_id option').nth(1).get_attribute('value')
                    simple.locator('#lines-0-product_id').select_option(option)
                    simple.locator('#lines-0-quantity').fill('1');simple.locator('#lines-0-unit_cost').fill('0.01')
                    with simple.expect_navigation(wait_until='domcontentloaded'):
                        simple.get_by_role('button',name='Lưu bản nháp',exact=True).press('Enter',no_wait_after=True)
                    simple.wait_for_url(re.compile(r'/business/purchases/\d+$'), wait_until='domcontentloaded')
                    expect(simple.locator('[data-document-total]')).to_have_text('0,01 ₫')
                    no_js.close()
                context.close()
                print(f'Inventory UI {role} {viewport}: real MySQL draft/complete/cancel, amounts, stock, roles and responsive passed.')
        browser.close()
    assert not errors and not assets,'Unexpected browser/asset errors: '+str(errors+assets)
    print('Stage 5 UI passed: 6 role/viewport flows plus no-JS draft. Test transaction history preserved; demo untouched.')


if __name__=='__main__':
    main()
