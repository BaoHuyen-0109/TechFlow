"""Exercise catalog CRUD in Chromium, exclusively against isolated test MySQL."""
import json
import argparse
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".browser-cache"))
from playwright.sync_api import sync_playwright, expect

BASE = "http://localhost:8001"


def capture(page, *, path, full_page=False):
    if full_page:
        # Chromium paints fixed elements at the current viewport offset in a
        # full-page shot. Capture from the top, preserving the focused field.
        page.evaluate("window.scrollTo({top:0, behavior:'instant'})")
    page.screenshot(path=path, full_page=full_page)


def provision():
    suffix, password = secrets.token_hex(6), secrets.token_urlsafe(24)
    accounts = {role: f"catalog-ui-{role}-{suffix}" for role in ("admin", "staff")}
    payload = json.dumps(dict(accounts=accounts, password=password))
    source = """
import json
from wsgi import app
from app.extensions import db
from app.models import User
assert app.config['APP_ENV'] == 'testing'
with app.app_context():
    assert db.engine.url.database == 'techflow_test' and db.engine.url.host == 'db-test'
    data = json.loads(PAYLOAD)
    for role, username in data['accounts'].items():
        user = User(username=username, role=role, full_name='Quản trị TechFlow' if role=='admin' else 'Nhân viên TechFlow')
        user.set_password(data['password'])
        db.session.add(user)
    db.session.commit()
print('Isolated catalog UI accounts ready; credentials not printed.')
""".replace("PAYLOAD", repr(payload))
    subprocess.run(["docker", "compose", "-f", "docker-compose.db-test.yml", "exec", "-T", "ui", "python", "-"],
                   cwd=ROOT, input=source, text=True, encoding="utf-8", check=True)
    return accounts, password


def assert_stored_prices(identifier, purchase, selling):
    """Read the actual DECIMAL columns after browser submits, without float math."""
    source = f"""
from decimal import Decimal
from wsgi import app
from app.extensions import db
from app.models import Product
assert app.config['APP_ENV'] == 'testing'
with app.app_context():
    assert db.engine.url.database == 'techflow_test' and db.engine.url.host == 'db-test'
    product = db.session.get(Product, {int(identifier)})
    assert product.purchase_price == Decimal({purchase!r})
    assert product.selling_price == Decimal({selling!r})
print('Browser price submission matches actual MySQL DECIMAL columns.')
"""
    subprocess.run(["docker", "compose", "-f", "docker-compose.db-test.yml", "exec", "-T", "ui", "python", "-"],
                   cwd=ROOT, input=source, text=True, encoding="utf-8", check=True)


def check_money_adapter(page):
    field = page.locator("#selling_price")
    for displayed, canonical in [("0", "0"), ("0,01", "0.01"), ("999.999.999.999,99", "999999999999.99"),
                                 ("15.000.000,50", "15000000.50"), ("15000000,50", "15000000.50"),
                                 ("1,001", "1.001"), ("18.500", "18500"), ("-0,01", "-0.01")]:
        field.fill(displayed)
        field.blur()
        assert page.locator("[name=selling_price]").input_value() == canonical
    field.fill("18.500.000.50")
    page.locator(".catalog-edit button[type=submit]").click()
    expect(field).to_be_focused()
    assert page.locator("#selling_price-errors").inner_text()
    assert page.locator(".catalog-edit").get_attribute("aria-busy") is None
    assert page.locator(".catalog-edit button[type=submit]").is_enabled()
    field.fill("18.000.000,50")
    field.blur()
    assert field.input_value() == "18.000.000,50"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot-prefix", default="stage4")
    prefix = parser.parse_args().screenshot_prefix
    if not prefix.replace("-", "").isalnum():
        raise ValueError("Invalid screenshot prefix")
    accounts, password = provision()
    screenshots = ROOT / "docs" / "screenshots"
    screenshots.mkdir(exist_ok=True)
    errors, assets, loading = [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for role in ("admin", "staff"):
            for viewport, width, height in [("desktop",1440,1000),("tablet",834,1112),("mobile",390,844)]:
                context = browser.new_context(viewport={"width":width,"height":height}, reduced_motion="reduce")
                page = context.new_page()
                # Controlled image fixtures exercise browser loading/CSP/fallback;
                # no server download, third-party dependency or real URL logging.
                page.route("https://images.example.invalid/*", lambda route: route.fulfill(
                    status=404 if "missing" in route.request.url else 200,
                    content_type="image/svg+xml",
                    body=b"" if "missing" in route.request.url else (ROOT / "app/static/images/product-placeholder.svg").read_bytes()))
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("response", lambda response: assets.append(response.url) if "/static/" in response.url and response.status >= 400 else None)
                # Record state during the real submit event, before navigation
                # suspends the old document. No request interception or fake saves.
                page.add_init_script("""
document.addEventListener('submit', (event) => {
  const form = event.target;
  if (event.defaultPrevented || form.method !== 'post' || !form.action.includes('/business/')) return;
  const checks = JSON.parse(sessionStorage.getItem('catalog-loading') || '[]');
  checks.push(form.getAttribute('aria-busy') === 'true' &&
              form.querySelector('button[type=submit]').disabled);
  sessionStorage.setItem('catalog-loading', JSON.stringify(checks));
});
""")
                page.goto(BASE + "/login")
                page.locator("#identity").fill(accounts[role])
                page.locator("#password").fill(password)
                page.get_by_role("button", name="Đăng nhập", exact=True).click()
                page.wait_for_url(f"**/{role}/dashboard")
                page.goto(BASE + "/staff/dashboard")
                capture(page, path=str(screenshots / f"{prefix}-{role}-business-{viewport}.png"), full_page=True)
                assert "giữa kỳ" not in page.locator("body").inner_text().lower()
                if width < 992:
                    page.get_by_role("button", name="Mở menu điều hướng").click()
                page.locator(".ws-navigation").get_by_role("link", name="Sản phẩm", exact=True).click()
                page.wait_for_url("**/business/products")
                assert page.locator('a.ws-nav-link.active').get_attribute("href") == "/business/products"
                assert page.locator(".ws-identity small").inner_text() == ("Quản trị viên" if role == "admin" else "Nhân viên")
                tag = secrets.token_hex(5).upper()
                ids = {}
                names = {"categories":f"Thiết bị văn phòng {tag}", "suppliers":f"Công ty Công nghệ {tag}", "products":f"Laptop TechFlow Pro 14 {tag}"}
                for kind in ("categories", "suppliers", "products"):
                    page.goto(BASE + f"/business/{kind}")
                    page.get_by_role("link", name="Thêm mới", exact=True).first.click()
                    page.locator("#sku" if kind == "products" else "#code").fill(f"UI-{tag}")
                    page.locator("#name").fill(names[kind])
                    if kind == "suppliers":
                        page.locator("#email").fill(f"supplier-{tag.lower()}@example.invalid")
                        page.locator("#phone").fill("0901234567")
                        page.locator("#address").fill("Thành phố Hồ Chí Minh")
                    elif kind == "products":
                        assert page.locator("#category_id").input_value() == "0"
                        page.locator("#category_id").select_option(ids["categories"])
                        page.locator("#business_id").select_option(ids["suppliers"])
                        page.locator("#brand").fill("TechFlow")
                        page.locator("#model").fill("Pro 14")
                        page.locator("#purchase_price").fill("15000000")
                        check_money_adapter(page)
                        assert page.locator("[name=stock_quantity]").count() == 0
                        preview = page.locator("[data-preview-status]")
                        page.locator("#image_url").fill("javascript:alert(1)")
                        expect(preview).to_have_text("URL chưa hợp lệ. Đang dùng ảnh mặc định.")
                        page.locator("#image_url").fill("https://images.example.invalid/missing.svg")
                        expect(preview).to_have_text("Không tải được ảnh. Đang dùng ảnh mặc định.")
                        capture(page, path=str(screenshots / f"{prefix}-{role}-image-fallback-{viewport}.png"), full_page=True)
                        page.locator("#image_url").fill("https://images.example.invalid/preview.svg")
                        expect(preview).to_have_text("Ảnh xem trước")
                        assert page.locator("[data-preview-image]").evaluate("e => e.naturalWidth > 0")
                    capture(page, path=str(screenshots / f"{prefix}-{role}-{kind}-form-{viewport}.png"), full_page=True)
                    page.locator(".catalog-edit button[type=submit]").click()
                    page.wait_for_url(f"**/business/{kind}/*")
                    assert not page.url.endswith("/new")
                    ids[kind] = page.url.rsplit("/", 1)[1]
                    if kind == "products":
                        assert_stored_prices(ids[kind], "15000000", "18000000.50")
                    assert page.get_by_role("heading", name=names[kind], exact=True).is_visible()
                    capture(page, path=str(screenshots / f"{prefix}-{role}-{kind}-detail-{viewport}.png"), full_page=True)
                    page.get_by_role("link", name="Chỉnh sửa", exact=True).click()
                    page.locator("#name").fill(names[kind] + " · Cập nhật")
                    if kind == "products":
                        assert page.locator("#category_id").input_value() == ids["categories"]
                        expect(page.locator("[data-preview-status]")).to_have_text("Ảnh xem trước")
                        capture(page, path=str(screenshots / f"{prefix}-{role}-{kind}-edit-{viewport}.png"), full_page=True)
                        page.locator("#selling_price").fill("-1")
                        with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith("/edit")) as response:
                            page.locator(".catalog-edit button[type=submit]").click()
                        assert response.value.status == 422
                        assert page.locator("#selling_price-errors").inner_text()
                        expect(page.locator("#selling_price")).to_be_focused()
                        assert page.locator("#name").input_value() == names[kind] + " · Cập nhật"
                        capture(page, path=str(screenshots / f"{prefix}-{role}-validation-{viewport}.png"), full_page=True)
                        page.locator("#purchase_price").fill("0,01")
                        page.locator("#selling_price").fill("18.500.000,50")
                    page.locator(".catalog-edit button[type=submit]").click()
                    page.wait_for_url(f"**/business/{kind}/{ids[kind]}")
                    if kind == "products":
                        assert_stored_prices(ids[kind], "0.01", "18500000.50")
                    assert page.get_by_role("heading", name=names[kind] + " · Cập nhật", exact=True).is_visible()
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    page.goto(BASE + f"/business/{kind}?q={tag}")
                    assert page.locator("tbody tr").count() == 1
                    assert names[kind] + " · Cập nhật" in page.locator("tbody").inner_text()
                    capture(page, path=str(screenshots / f"{prefix}-{role}-{kind}-{viewport}.png"), full_page=True)
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    if width == 390:
                        assert page.locator(".table-responsive").evaluate("e => e.scrollWidth > e.clientWidth")
                page.locator("#category_id").select_option(ids["categories"])
                page.locator("#business_id").select_option(ids["suppliers"])
                page.get_by_role("button", name="Áp dụng").click()
                assert page.locator("tbody tr").count() == 1
                assert "18.500.000,50 ₫" in page.locator("tbody").inner_text()
                for kind in ("categories", "suppliers"):
                    page.goto(BASE + f"/business/{kind}/{ids[kind]}")
                    page.get_by_role("button", name="Xóa dữ liệu", exact=True).click()
                    page.locator("#delete-modal").wait_for(state="visible")
                    assert page.locator("#delete-modal").is_visible()
                    assert names[kind] in page.locator("[data-delete-name]").inner_text()
                    page.get_by_role("button", name="Hủy", exact=True).click()
                    page.locator("#delete-modal").wait_for(state="hidden")
                    page.get_by_role("button", name="Xóa dữ liệu", exact=True).click()
                    page.locator("#delete-modal").wait_for(state="visible")
                    with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith("/delete")) as response:
                        page.get_by_role("button", name="Xác nhận xóa").click()
                    assert response.value.status == 409
                    expected_error = "Danh mục này đang được sử dụng" if kind == "categories" else "Không thể xóa nhà cung cấp vì còn dữ liệu liên kết"
                    assert expected_error in page.locator(".alert-danger").inner_text()
                for kind in ("products", "categories", "suppliers"):
                    page.goto(BASE + f"/business/{kind}/{ids[kind]}")
                    page.get_by_role("button", name="Xóa dữ liệu", exact=True).click()
                    page.locator("#delete-modal").wait_for(state="visible")
                    if kind == "products":
                        capture(page, path=str(screenshots / f"{prefix}-{role}-delete-modal-{viewport}.png"))
                    page.get_by_role("button", name="Xác nhận xóa").click()
                    page.wait_for_url(BASE + f"/business/{kind}")
                    page.locator("#q").fill(tag)
                    page.get_by_role("button", name="Áp dụng").click()
                    assert page.locator("tbody tr").count() == 0
                    assert page.get_by_role("heading", name="Chưa có kết quả phù hợp").is_visible()
                if role == "staff":
                    assert page.goto(BASE + "/admin/dashboard").status == 403
                else:
                    page.goto(BASE + "/business/products")
                    page.get_by_role("link", name="Quay về quản trị").click()
                    page.wait_for_url("**/admin/dashboard")
                page.get_by_role("button", name="Đăng xuất", exact=True).click()
                page.wait_for_url("**/login")
                loading.extend(page.evaluate("JSON.parse(sessionStorage.getItem('catalog-loading') || '[]')"))
                context.close()
                print(f"Catalog CRUD {role} {viewport} {width}x{height}: passed.")
        browser.close()
    assert not errors and not assets, "Browser or asset error detected"
    assert loading and all(loading), "Submit loading state missing"
    print(f"Catalog UI passed: 6 role/viewport flows, 18 CRUD lifecycles, {len(loading)} POST loading checks. Demo untouched.")


if __name__ == "__main__":
    main()
