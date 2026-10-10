"""Stage 6 browser acceptance on the isolated Docker/MySQL test application."""
import json
import secrets
import subprocess
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect
from verify_catalog_ui import ROOT, BASE, provision, capture


def test_database(source):
    guarded = """
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from wsgi import app
from app.extensions import db
from app.models import Category, Product
from app.services.dashboard_service import load_dashboard
assert app.config['APP_ENV'] == 'testing'
with app.app_context():
    assert db.engine.url.database == 'techflow_test' and db.engine.url.host == 'db-test'
BODY
""".replace("BODY", "\n".join("    " + line for line in source.splitlines()))
    return subprocess.check_output(
        ["docker", "compose", "-f", "docker-compose.db-test.yml", "exec", "-T", "ui", "python", "-"],
        cwd=ROOT, input=guarded, text=True, encoding="utf-8")


def main():
    accounts, password = provision()
    tag = "DASHBOARD-" + secrets.token_hex(6).upper()
    test_database(f"""
category = Category(code={tag!r}, name='Thiết bị kiểm chứng Dashboard ' + {tag!r})
db.session.add(category)
db.session.flush()
now = datetime.now(timezone.utc).replace(tzinfo=None)
for index, active in enumerate([True, True, False]):
    db.session.add(Product(sku={tag!r} + '-' + str(index), name='SSD TechFlow kiểm thử ' + str(index),
        category_id=category.id, purchase_price=Decimal('1234.56'), selling_price=Decimal('1500.01'),
        stock_quantity=index, reorder_level=1, is_active=active,
        created_at=now, updated_at=now+timedelta(minutes=1)))
db.session.commit()
""")
    try:
        expected = json.loads(test_database("print(json.dumps({role: load_dashboard(role) for role in ['admin','staff']}, default=str))"))
        errors, assets = [], []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for role in ("admin", "staff"):
                for label, width, height in [("desktop",1440,1000),("tablet",834,1112),("mobile",390,844)]:
                    context = browser.new_context(viewport={"width":width,"height":height}, reduced_motion="reduce")
                    page = context.new_page()
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on("response", lambda response: assets.append(response.url) if "/static/" in response.url and response.status >= 400 else None)
                    page.goto(BASE + "/login")
                    page.locator("#identity").fill(accounts[role])
                    page.locator("#password").fill(password)
                    page.get_by_role("button", name="Đăng nhập", exact=True).click()
                    page.wait_for_url(f"**/{role}/dashboard")
                    page.goto(BASE + "/staff/dashboard?role=admin")
                    stats = expected[role]
                    for key in ("products", "categories", "suppliers", "low_stock"):
                        expect(page.locator(f'[data-kpi="{key}"]')).to_have_text(str(stats["totals"][key]))
                    if role == "admin":
                        value = stats["totals"]["inventory_value"]
                        from decimal import Decimal
                        formatted = format(Decimal(value), ",.2f").replace(",","_").replace(".",",").replace("_",".") + " ₫"
                        expect(page.locator('[data-kpi="inventory_value"]')).to_have_text(formatted)
                        expect(page.get_by_role("link",name="Quay về quản trị",exact=True)).to_be_visible()
                    else:
                        assert "inventory_value" not in stats["totals"]
                        assert page.locator('[data-kpi="inventory_value"]').count() == 0
                        assert "Giá trị tồn kho ước tính" not in page.locator("body").inner_text()
                    chart = page.locator("[data-category-chart]")
                    expect(chart).to_have_attribute("data-chart-ready", "true")
                    assert json.loads(chart.get_attribute("data-chart-data")) == stats["categories"]
                    actual = page.locator("#category-chart").evaluate("canvas => Chart.getChart(canvas).data.datasets[0].data")
                    assert actual == [row["count"] for row in stats["categories"]]
                    assert sum(actual) == stats["totals"]["products"]
                    chart.locator("summary").click()
                    assert chart.locator("[data-category-count]").all_text_contents() == [str(row["count"]) for row in stats["categories"]]
                    chart.locator("summary").click()
                    assert page.locator("[data-low-stock-id]").evaluate_all("rows => rows.map(r => Number(r.dataset.lowStockId))") == [row["id"] for row in stats["low_stock"]]
                    assert page.locator("[data-recent-id]").evaluate_all("rows => rows.map(r => Number(r.dataset.recentId))") == [row["id"] for row in stats["recent"]]
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    capture(page, path=str(ROOT / "docs/screenshots" / f"stage6-after-{role}-{label}.png"), full_page=True)
                    page.locator("[data-low-stock-id] a").first.click()
                    page.wait_for_url("**/business/products/*")
                    assert page.locator(".catalog-detail").is_visible()
                    page.goto(BASE + "/staff/dashboard")
                    with page.expect_response(lambda response: response.request.method == "GET" and urlsplit(response.url).path == "/staff/dashboard") as refreshed:
                        page.get_by_role("button", name="Làm mới", exact=True).click()
                    assert refreshed.value.status == 200
                    assert urlsplit(page.url).path == "/staff/dashboard"
                    expect(page.locator("[data-category-chart]")).to_have_attribute("data-chart-ready", "true")
                    if label == "desktop":
                        state = context.storage_state()
                        fallback = browser.new_context(storage_state=state, viewport={"width":width,"height":height})
                        fallback_page = fallback.new_page()
                        fallback_page.route("**/vendor/chartjs/chart.umd.min.js", lambda route: route.abort())
                        fallback_page.goto(BASE + "/staff/dashboard")
                        expect(fallback_page.locator("[data-chart-status]")).to_have_text("Chưa thể hiển thị biểu đồ. Số liệu vẫn có trong bảng bên dưới.")
                        assert fallback_page.locator("[data-category-chart] details").get_attribute("open") is not None
                        capture(fallback_page,path=str(ROOT / "docs/screenshots" / f"stage6-chart-fallback-{role}.png"),full_page=True)
                        fallback.close()
                        no_js = browser.new_context(storage_state=state, java_script_enabled=False, viewport={"width":width,"height":height})
                        no_js_page = no_js.new_page()
                        no_js_page.goto(BASE + "/staff/dashboard")
                        expect(no_js_page.locator('[data-kpi="products"]')).to_have_text(str(stats["totals"]["products"]))
                        assert no_js_page.locator("[data-category-chart] details").get_attribute("open") is not None
                        assert no_js_page.locator("[data-category-count]").count() == len(stats["categories"])
                        capture(no_js_page,path=str(ROOT / "docs/screenshots" / f"stage6-no-js-{role}.png"),full_page=True)
                        no_js.close()
                    if role == "staff":
                        assert page.goto(BASE + "/admin/dashboard").status == 403
                    else:
                        page.get_by_role("link", name="Quay về quản trị", exact=True).click()
                        page.wait_for_url("**/admin/dashboard")
                        assert page.locator(".ws-identity small").inner_text() == "Quản trị viên"
                    context.close()
                    print(f"Dashboard {role} {label}: real KPI/chart/rows, navigation, responsive passed.")
            browser.close()
        assert not errors and not assets, "Unexpected browser/asset failure"
        print("Dashboard UI passed: 6 role/viewport flows, 2 script-failure fallbacks, 2 no-JS views. Demo untouched.")
    finally:
        test_database(f"""
for item in db.session.scalars(db.select(Product).where(Product.sku.startswith({tag!r}))):
    db.session.delete(item)
db.session.flush()
for item in db.session.scalars(db.select(Category).where(Category.code == {tag!r})):
    db.session.delete(item)
db.session.commit()
""")


if __name__ == "__main__":
    main()
