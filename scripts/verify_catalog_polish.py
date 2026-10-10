"""Final UI acceptance: filter state/paging/navigation and no-JS Decimal fallback.

All fixtures and mutations are restricted to Docker's isolated techflow_test DB.
"""
import json
import secrets
import subprocess
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright, expect

from verify_catalog_ui import ROOT, BASE, provision, assert_stored_prices


def database(source):
    guarded = """
import json
from wsgi import app
from app.extensions import db
from app.models import Category, Business, Product
from decimal import Decimal
assert app.config['APP_ENV'] == 'testing'
with app.app_context():
    assert db.engine.url.database == 'techflow_test' and db.engine.url.host == 'db-test'
BODY
""".replace("BODY", "\n".join("    " + line for line in source.splitlines()))
    return subprocess.check_output(
        ["docker", "compose", "-f", "docker-compose.db-test.yml", "exec", "-T", "ui", "python", "-"],
        cwd=ROOT, input=guarded, text=True, encoding="utf-8")


def sign_in(page, username, password):
    page.goto(BASE + "/login")
    page.locator("#identity").fill(username)
    page.locator("#password").fill(password)
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    page.wait_for_url("**/dashboard")


def navigate_click(page, locator):
    # Wait for the GET document before asserting row counts or URL filter state.
    with page.expect_navigation(wait_until='domcontentloaded'):
        locator.click(no_wait_after=True)


def main():
    accounts, password = provision()
    tag = "FINAL-" + secrets.token_hex(6).upper()
    fixture = json.loads(database(f"""
categories, suppliers = [], []
for index in range(11):
    code = {tag!r} + '-' + str(index).zfill(2)
    category = Category(code=code, name=code, is_active=True)
    supplier = Business(code=code, name=code, is_active=True)
    db.session.add_all([category, supplier])
    categories.append(category)
    suppliers.append(supplier)
db.session.flush()
for index in range(11):
    code = {tag!r} + '-' + str(index).zfill(2)
    db.session.add(Product(sku=code, name=code, category_id=categories[0].id,
        business_id=suppliers[0].id, purchase_price=Decimal('0.01'),
        selling_price=Decimal('15000000.50'), is_active=True))
db.session.commit()
print(json.dumps(dict(category=categories[0].id, supplier=suppliers[0].id)))
"""))
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for role in ("admin", "staff"):
                for label, width, height in [("desktop",1440,1000),("tablet",834,1112),("mobile",390,844)]:
                    context = browser.new_context(viewport={"width":width,"height":height}, reduced_motion="reduce")
                    page = context.new_page()
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    sign_in(page, accounts[role], password)
                    for kind in ("categories", "suppliers", "products"):
                        page.goto(BASE + f"/business/{kind}")
                        page.locator("#q").fill(tag)
                        page.locator("#status").select_option("active")
                        page.locator("#sort").select_option("name")
                        page.locator("#per_page").select_option("10")
                        if kind == "products":
                            page.locator("#category_id").select_option(str(fixture["category"]))
                            page.locator("#business_id").select_option(str(fixture["supplier"]))
                        navigate_click(page, page.get_by_role("button", name="Áp dụng", exact=True))
                        assert page.locator("tbody tr").count() == 10
                        names = page.locator(".catalog-record-name").all_text_contents()
                        assert names == sorted(names)
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                        filters = page.locator(".catalog-filters").bounding_box()
                        if width == 1440 and kind != "products":
                            assert filters["height"] < 120, "Short filters should occupy one row"
                        original = parse_qs(urlsplit(page.url).query)
                        navigate_click(page, page.get_by_role("link", name="Tiếp", exact=True))
                        current = parse_qs(urlsplit(page.url).query)
                        assert current.pop("page") == ["2"]
                        assert current == original
                        assert page.locator("tbody tr").count() == 1
                        navigate_click(page, page.get_by_role("link", name="Trước", exact=True))
                        assert page.locator("tbody tr").count() == 10
                        page.locator("#per_page").select_option("20")
                        navigate_click(page, page.get_by_role("button", name="Áp dụng", exact=True))
                        assert page.locator("tbody tr").count() == 11
                        assert "page" not in parse_qs(urlsplit(page.url).query)
                        page.locator("#status").select_option("inactive")
                        navigate_click(page, page.get_by_role("button", name="Áp dụng", exact=True))
                        assert page.get_by_role("heading", name="Chưa có kết quả phù hợp").is_visible()
                        navigate_click(page, page.get_by_role("link", name="Xóa lọc", exact=True))
                        assert page.url == BASE + f"/business/{kind}"
                        assert page.locator("#q").input_value() == ""
                        assert page.locator("#status").input_value() == ""
                        # The account menu is a real read-only section, not a fake profile page.
                        if width < 992:
                            page.get_by_role("button", name="Mở menu điều hướng").click()
                        page.get_by_role("link", name="Thông tin cá nhân", exact=True).click()
                        page.wait_for_url("**/staff/dashboard#session")
                        expect(page.locator("#session")).to_be_in_viewport()
                        assert accounts[role] in page.locator("#session").inner_text()
                    print(f"Filter/pagination/profile {role} {label}: 3 modules passed.")
                    context.close()
            # With scripting disabled, the original canonical fields and backend remain usable.
            context = browser.new_context(java_script_enabled=False, viewport={"width":1440,"height":1000})
            page = context.new_page()
            sign_in(page, accounts["admin"], password)
            page.goto(BASE + "/business/products/new")
            assert page.locator("#selling_price").get_attribute("type") == "number"
            page.locator("#sku").fill(tag + "-NOJS")
            page.locator("#name").fill(tag + "-NOJS")
            page.locator("#category_id").select_option(str(fixture["category"]))
            page.locator("#purchase_price").fill("999999999999.99")
            page.locator("#selling_price").fill("0.01")
            page.locator(".catalog-edit button[type=submit]").click()
            page.wait_for_url("**/business/products/*")
            assert not page.url.endswith("/new")
            assert_stored_prices(page.url.rsplit("/",1)[1], "999999999999.99", "0.01")
            page.get_by_role("link", name="Chỉnh sửa", exact=True).click()
            page.locator("#selling_price").fill("-0.01")
            with page.expect_response(lambda response: response.request.method == "POST") as response:
                page.locator(".catalog-edit button[type=submit]").click()
            assert response.value.status == 422
            assert page.locator("#selling_price-errors").inner_text()
            context.close()
            browser.close()
        assert not errors, "JavaScript error detected"
        print("Final UI acceptance passed: 18 module filter/paging/profile flows; no-JS CRUD/precision/validation passed.")
    finally:
        # Delete only uniquely named fixtures created by this invocation, products first.
        database(f"""
for model, field in [(Product, Product.sku), (Category, Category.code), (Business, Business.code)]:
    for record in db.session.scalars(db.select(model).where(field.startswith({tag!r}))):
        db.session.delete(record)
    db.session.flush()
db.session.commit()
print("Only this run's isolated fixtures removed; demo unchanged.")
""")


if __name__ == "__main__":
    main()
