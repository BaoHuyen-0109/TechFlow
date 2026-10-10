"""Warranty and grouped navigation acceptance; fixtures only on db-test."""
import json
import re
import secrets
import time
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright,expect
from verify_catalog_ui import ROOT,BASE,provision,capture
from verify_dashboard_ui import test_database


def main():
    accounts,password=provision();errors=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        for role in ['admin','staff']:
            for viewport,width,height in [('desktop',1440,1000),('tablet',834,1112),('mobile',390,844)]:
                tag='UI52-'+secrets.token_hex(5).upper()
                fixture=json.loads(test_database(f'''
from app.models import Business,User,SalesOrderItem,SalesOrder
from app.services.transaction_service import create_document,transition
from app.services.warranty_service import create_ticket
admin=db.session.scalar(db.select(User.id).where(User.username=={accounts['admin']!r}))
staff=db.session.scalar(db.select(User.id).where(User.username=={accounts['staff']!r}))
category=Category(code={tag!r},name='Thiết bị hậu mãi '+{tag!r})
supplier=Business(code={tag!r},name='Supplier warranty test')
db.session.add_all([category,supplier]);db.session.flush()
product=Product(sku={tag!r},name='Máy lọc nước demo kiểm thử',category_id=category.id,business_id=supplier.id,purchase_price=Decimal('1234.56'),selling_price=Decimal('2345.67'),warranty_enabled=True,warranty_months=12,warranty_notes='Bảo hành lỗi kỹ thuật; kiểm tra thực tế trước khi chấp nhận.')
db.session.add(product);db.session.commit()
incoming=create_document('purchases',admin,dict(business_id=supplier.id),[dict(product_id=product.id,quantity=10,unit_cost='1234.56')]);transition('purchases',admin,incoming,'complete')
oid=create_document('sales',admin,dict(customer_name='Khách bảo hành '+{tag!r},customer_phone='0901234567',notes='PRIVATE-ORDER-WARRANTY'),[dict(product_id=product.id,quantity=3)]);transition('sales',admin,oid,'complete')
db.session.rollback();item=db.session.scalar(db.select(SalesOrderItem).where(SalesOrderItem.order_id==oid))
hidden=create_ticket(admin,item.id,3,None,'PRIVATE-OTHER-TICKET')
print(json.dumps(dict(item=item.id,order=oid,product=product.id,hidden=hidden,admin=admin,staff=staff)))
'''))
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce',locale='vi-VN')
                page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(BASE+'/login');page.locator('#identity').fill(accounts[role]);page.locator('#password').fill(password)
                page.get_by_role('button',name='Đăng nhập',exact=True).click();page.wait_for_url('**/'+role+'/dashboard')
                page.goto(BASE+'/staff/dashboard')
                if width<992:
                    page.get_by_role('button',name='Mở menu điều hướng').click()
                    page.wait_for_selector('#workspace-sidebar.show:not(.showing)',state='visible')
                group=page.locator('[data-nav-group="aftersales"]');summary=group.locator('summary')
                summary.focus();page.keyboard.press('Enter');expect(group).to_have_attribute('open','')
                page.keyboard.press('Space');expect(group).not_to_have_attribute('open','')
                summary.click();expect(summary).to_have_attribute('aria-expanded','true')
                if width>=992:
                    page.locator('[data-sidebar-collapse]').click();expect(page.locator('body')).to_have_class(re.compile('workspace-collapsed'))
                    summary.click();expect(page.locator('body')).not_to_have_class(re.compile('workspace-collapsed'))
                    expect(group).to_have_attribute('open','')
                page.get_by_role('link',name='Tra cứu bảo hành',exact=True).click();page.wait_for_url('**/warranties/lookup')
                expect(page.locator('[data-nav-group="aftersales"]')).to_have_attribute('open','')
                expect(page.locator('a.ws-nav-link.active')).to_have_attribute('href','/business/warranties/lookup')
                page.locator('#q').fill(tag)
                with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Tra cứu',exact=True).click(no_wait_after=True)
                expect(page.locator('[data-lookup-item]')).to_have_count(1)
                assert 'PRIVATE-ORDER-WARRANTY' not in page.locator('body').inner_text()
                if role=='staff':
                    assert page.request.get(BASE+f'/business/sales/{fixture["order"]}').status==404
                    assert page.request.get(BASE+f'/business/warranties/{fixture["hidden"]}').status==404
                    assert page.request.get(BASE+f'/business/warranties/legacy/{fixture["item"]}').status==403
                page.get_by_role('link',name='Tiếp nhận',exact=True).click();page.wait_for_url('**/warranties/new/*')
                page.locator('#serial').fill('SN-'+tag);page.locator('#issue').fill('Máy không chạy, khách cần kiểm tra.')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                if viewport in ['desktop','mobile']:
                    page.locator('.ws-content').evaluate("main=>main.insertAdjacentHTML('afterbegin','<p class=wr-notice>DỮ LIỆU KIỂM THỬ RIÊNG — KHÔNG PHẢI DATABASE DEMO</p>')")
                    capture(page,path=str(ROOT/'docs/screenshots'/f'stage52-{role}-{viewport}-intake.png'),full_page=True)
                with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Lưu phiếu tiếp nhận',exact=True).click(no_wait_after=True)
                page.wait_for_url(re.compile(r'/business/warranties/\d+$'));ticket_url=page.url
                expect(page.locator('h1')).to_have_text(re.compile('BH-'))
                for target,label in [('processing','Đang xử lý'),('completed','Hoàn thành'),('returned','Đã trả khách')]:
                    page.locator('#target').select_option(target);page.locator('#inspection_result').fill('Đã đối chiếu máy, kiểm tra và xử lý lỗi kỹ thuật.')
                    page.locator('#confirmed').select_option('yes')
                    with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Cập nhật xử lý',exact=True).click(no_wait_after=True)
                    expect(page.locator('.catalog-heading .wr-state')).to_have_text(label)
                expect(page.locator('.wr-history li')).to_have_count(4)
                test_database(f'assert db.session.get(Product,{fixture["product"]}).stock_quantity==7')
                if viewport in ['desktop','mobile']:
                    page.locator('.ws-content').evaluate("main=>main.insertAdjacentHTML('afterbegin','<p class=wr-notice>DỮ LIỆU KIỂM THỬ RIÊNG — KHÔNG PHẢI DATABASE DEMO</p>')")
                    capture(page,path=str(ROOT/'docs/screenshots'/f'stage52-{role}-{viewport}-returned.png'),full_page=True)
                if role=='admin':
                    if viewport=='desktop':
                        page.goto(BASE+f'/business/warranties/{fixture["hidden"]}')
                        page.locator('#assignee').select_option(str(fixture['staff']))
                        with page.expect_navigation(wait_until='domcontentloaded'):
                            page.get_by_role('button',name='Phân công xử lý',exact=True).click(no_wait_after=True)
                        expect(page.locator('.wr-history')).to_contain_text('Phân công')
                        legacy=json.loads(test_database(f'''
from app.models import SalesOrder,SalesOrderItem
old=SalesOrder(order_code={tag!r}+'-OLD',created_by={fixture['admin']},customer_name='Khách đơn cũ kiểm thử',order_date=datetime(2025,1,31),status='completed',total_amount=Decimal('2345.67'))
db.session.add(old);db.session.flush()
item=SalesOrderItem(order_id=old.id,product_id={fixture['product']},quantity=1,unit_price=Decimal('2345.67'),line_total=Decimal('2345.67'))
db.session.add(item);db.session.commit();print(json.dumps(dict(item=item.id,order=old.id)))
'''))
                        page.goto(BASE+'/business/warranties/lookup?q='+tag+'-OLD')
                        page.get_by_role('link',name='Xác minh đơn cũ',exact=True).click()
                        page.locator('#starts_on').fill(datetime.now(timezone(timedelta(hours=7))).date().isoformat())
                        page.locator('#months').fill('12');page.locator('#reason').fill('Đã kiểm tra chứng từ thử nghiệm, không suy đoán từ sản phẩm.')
                        with page.expect_navigation(wait_until='domcontentloaded'):
                            page.get_by_role('button',name='Xác nhận chính sách',exact=True).click(no_wait_after=True)
                        page.locator('#issue').fill('Khách báo máy bị va đập.')
                        with page.expect_navigation(wait_until='domcontentloaded'):
                            page.get_by_role('button',name='Lưu phiếu tiếp nhận',exact=True).click(no_wait_after=True)
                        page.locator('#target').select_option('rejected');page.locator('#inspection_result').fill('Kiểm tra thấy hư hỏng ngoại lực.')
                        page.locator('#rejection_reason').fill('Không thuộc điều kiện bảo hành dù còn hạn.');page.locator('#confirmed').select_option('yes')
                        with page.expect_navigation(wait_until='domcontentloaded'):
                            page.get_by_role('button',name='Cập nhật xử lý',exact=True).click(no_wait_after=True)
                        expect(page.locator('.catalog-heading .wr-state')).to_have_text('Từ chối')
                        expect(page.locator('.alert-warning')).to_contain_text('Không thuộc điều kiện')
                        test_database(f'from app.models import SalesOrder\nassert db.session.get(SalesOrder,{legacy["order"]}).completed_at is None')
                        print('Admin browser: assignment, verified legacy intake and reasoned rejection passed.',flush=True)
                    page.goto(BASE+'/staff/dashboard');page.get_by_role('link',name='Quay về quản trị',exact=True).click();page.wait_for_url('**/admin/dashboard')
                    if width<992:page.get_by_role('button',name='Mở menu điều hướng').click()
                    page.get_by_role('link',name='Không gian kinh doanh',exact=True).click();page.wait_for_url('**/staff/dashboard')
                else:
                    assert page.request.get(BASE+'/admin/dashboard').status==403
                    if viewport=='desktop':
                        test_database(f'from app.services.warranty_service import handle_ticket\nhandle_ticket({fixture["admin"]},{fixture["hidden"]},"assign","received",assignee={fixture["staff"]})')
                        page.goto(BASE+f'/business/warranties/{fixture["hidden"]}')
                        page.locator('#target').select_option('processing');page.locator('#inspection_result').fill('Đã kiểm tra phiếu được phân công và chính sách.');page.locator('#confirmed').select_option('yes')
                        with page.expect_navigation(wait_until='domcontentloaded'):
                            page.get_by_role('button',name='Cập nhật xử lý',exact=True).click(no_wait_after=True)
                        expect(page.locator('.catalog-heading .wr-state')).to_have_text('Đang xử lý')
                        print('Staff browser: assigned Admin-created ticket is accessible and actionable; sale remains restricted.',flush=True)
                print(f'Warranty {role} {viewport}: keyboard, menus, lookup, intake, lifecycle, privacy and stock passed.',flush=True)
                context.close();time.sleep(7)
        # Native details remain usable without JavaScript.
        context=browser.new_context(java_script_enabled=False,viewport={'width':1440,'height':1000});page=context.new_page()
        page.goto(BASE+'/login');page.locator('#identity').fill(accounts['staff']);page.locator('#password').fill(password)
        page.get_by_role('button',name='Đăng nhập',exact=True).click();page.wait_for_url('**/staff/dashboard')
        page.locator('[data-nav-group="aftersales"]>summary').click();page.get_by_role('link',name='Tra cứu bảo hành',exact=True).click()
        expect(page.get_by_role('heading',name='Tra cứu bảo hành',exact=True)).to_be_visible();context.close();browser.close()
    assert not errors,errors
    print('Warranty browser acceptance: 6 role/viewport flows and no-JS navigation passed.')


if __name__=='__main__':main()
