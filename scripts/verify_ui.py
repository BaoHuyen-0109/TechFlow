"""Browser verification of separate role workspaces against isolated test MySQL."""
from pathlib import Path
import json
import argparse
import os
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".browser-cache"))
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot-prefix", default="access")
    prefix = parser.parse_args().screenshot_prefix
    if not prefix.replace("-", "").isalnum():
        raise ValueError("Invalid screenshot prefix")
    suffix = secrets.token_hex(6)
    password = secrets.token_urlsafe(24)
    accounts = {role: f"ui-{role}-{suffix}" for role in ("admin", "staff")}
    payload = json.dumps({"accounts": accounts, "password": password})
    source = """
import json
import argparse
from wsgi import app
from app.extensions import db
from app.models import User
assert app.config['APP_ENV'] == 'testing'
with app.app_context():
    assert db.engine.url.database == 'techflow_test' and db.engine.url.host == 'db-test'
    data = json.loads(PAYLOAD)
    for role, username in data['accounts'].items():
        user = User(username=username, email=username+'@example.invalid', role=role,
                    full_name='Quản trị TechFlow' if role=='admin' else 'Nhân viên TechFlow')
        user.set_password(data['password'])
        db.session.add(user)
    db.session.commit()
print('Isolated UI accounts ready; credentials not printed.')
""".replace("PAYLOAD", repr(payload))
    subprocess.run(["docker", "compose", "-f", "docker-compose.db-test.yml", "exec", "-T", "ui", "python", "-"],
                   cwd=ROOT, input=source, text=True, encoding="utf-8", check=True)
    screenshots = ROOT / "docs" / "screenshots"
    screenshots.mkdir(exist_ok=True)
    errors, asset_errors = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for role in ("admin", "staff"):
            for label, width, height in [("desktop", 1440, 1000), ("tablet", 834, 1112), ("mobile", 390, 844)]:
                context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
                page = context.new_page()
                login_posts = []
                page.on("request", lambda request: login_posts.append(1)
                        if request.method == "POST" and request.url.endswith("/login") else None)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("response", lambda response: asset_errors.append(response.url)
                        if "/static/" in response.url and response.status >= 400 else None)
                assert page.goto("http://localhost:8001/login").status == 200
                page.evaluate("document.fonts.ready")
                if role == "admin":
                    page.screenshot(path=str(screenshots / f"{prefix}-login-{label}.png"), full_page=True)
                page.locator("#identity").fill(accounts[role] + ("@example.invalid" if role == "staff" else ""))
                page.locator("#password").fill(password)
                page.get_by_role("button", name="Hiện mật khẩu").click()
                assert page.locator("#password").get_attribute("type") == "text"
                page.get_by_role("button", name="Ẩn mật khẩu").click()
                page.get_by_role("button", name="Đăng nhập", exact=True).click()
                page.wait_for_url(f"**/{role}/dashboard")
                heading = "Tổng quan quản trị" if role == "admin" else "Tổng quan kinh doanh"
                assert page.get_by_role("heading", name=heading, exact=True).is_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                assert page.locator("a.ws-nav-link.active[aria-current=page]").count() == 1
                assert page.locator(".ws-pending a, .business-shortcut[aria-disabled=true] a, .business-shortcut[aria-disabled=true] button").count() == 0
                assert page.locator(".ws-topbar").is_visible()
                assert page.locator(".ws-identity small").text_content() == ("Quản trị viên" if role == "admin" else "Nhân viên")
                page.screenshot(path=str(screenshots / f"{prefix}-{role}-{label}.png"), full_page=True)
                if width >= 992:
                    collapse = page.locator("[data-sidebar-collapse]")
                    collapse.click()
                    assert collapse.get_attribute("aria-expanded") == "false"
                    assert page.locator("#workspace-sidebar").bounding_box()["width"] == 80
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    page.screenshot(path=str(screenshots / f"{prefix}-{role}-collapsed.png"), full_page=True)
                    page.get_by_role("button", name="Mở rộng thanh điều hướng").click()
                    assert page.locator("#workspace-sidebar").bounding_box()["width"] == 244
                else:
                    page.get_by_role("button", name="Mở menu điều hướng").click()
                    page.wait_for_selector("#workspace-sidebar.show", state="visible")
                # Every actual navigation link has a real page/section destination.
                links = page.locator("a.ws-nav-link")
                for link in links.all():
                    href = link.get_attribute("href")
                    path = href.split("#")[0]
                    assert path in ({"/admin/dashboard", "/staff/dashboard"} if role == "admin" else {"/staff/dashboard", "/business/products", "/business/categories", "/business/suppliers", "/business/sales", "/business/inventory", "/business/customers"})
                    if "#" in href:
                        assert page.locator("#" + href.split("#")[1]).count() == 1
                    link.scroll_into_view_if_needed()
                    assert link.is_visible()
                target = links.last
                before = target.evaluate("(element) => getComputedStyle(element).backgroundColor")
                target.hover()
                after = target.evaluate("(element) => getComputedStyle(element).backgroundColor")
                assert before != after
                target.focus()
                page.keyboard.press("Shift+Tab")
                page.keyboard.press("Tab")
                assert target.evaluate("(element) => element === document.activeElement")
                assert target.evaluate("(element) => getComputedStyle(element).outlineStyle") != "none"
                links.first.scroll_into_view_if_needed()
                if width < 992:
                    page.screenshot(path=str(screenshots / f"{prefix}-{role}-menu-{label}.png"))
                    page.get_by_role("button", name="Đóng menu").click()
                    page.wait_for_selector("#workspace-sidebar:not(.show)", state="attached")
                # Legacy routing and cross-role backend restrictions.
                assert page.goto("http://localhost:8001/dashboard").url.endswith(f"/{role}/dashboard")
                if role == "admin":
                    assert page.goto("http://localhost:8001/admin").url.endswith("/admin/dashboard")
                    if width < 992:
                        page.get_by_role("button", name="Mở menu điều hướng").click()
                        page.wait_for_selector("#workspace-sidebar.show", state="visible")
                    page.get_by_role("link", name="Không gian kinh doanh", exact=True).click()
                    page.wait_for_url("**/staff/dashboard")
                    assert page.locator("body").get_attribute("class").endswith("staff-workspace")
                    assert page.locator(".ws-identity small").text_content() == "Quản trị viên"
                    assert page.locator(".staff-session .ws-chip").text_content().strip() == "Quản trị viên"
                    assert page.locator(".ws-identity strong").text_content() == "Quản trị TechFlow"
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    assert page.locator(".breadcrumb-item.active").text_content().strip() == "Kinh doanh"
                    assert page.locator("a[aria-current=page]").get_attribute("href") == "/staff/dashboard"
                    page.screenshot(path=str(screenshots / f"{prefix}-admin-business-{label}.png"), full_page=True)
                    page.get_by_role("link", name="Quay về quản trị", exact=True).click()
                    page.wait_for_url("**/admin/dashboard")
                    assert page.locator("body").get_attribute("class").endswith("admin-workspace")
                    assert len(login_posts) == 1
                    page.screenshot(path=str(screenshots / f"{prefix}-admin-return-{label}.png"), full_page=True)
                else:
                    assert page.get_by_role("link", name="Quay về quản trị").count() == 0
                    assert page.locator("a[href*='/admin']").count() == 0
                    assert page.goto("http://localhost:8001/admin").status == 403
                    assert page.goto("http://localhost:8001/admin/dashboard").status == 403
                    assert page.locator("body").get_attribute("class").endswith("staff-workspace")
                    page.screenshot(path=str(screenshots / f"{prefix}-staff-403-{label}.png"), full_page=True)
                assert page.goto("http://localhost:8001/missing-ui-page").status == 404
                page.get_by_role("button", name="Đăng xuất", exact=True).click()
                page.wait_for_url("**/login")
                assert "/login?" in page.goto(f"http://localhost:8001/{role}/dashboard").url
                context.close()
                print(f"Browser {role} {label} {width}x{height}: all checks passed.")
        browser.close()
    assert not errors, "Browser JavaScript pageerror detected"
    assert not asset_errors, "Local asset failed to load"
    print("Browser verification passed for both roles at all three viewports. Demo unchanged.")


if __name__ == "__main__":
    main()
