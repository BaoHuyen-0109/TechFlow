"""Browser checks against the isolated UI Docker profile at localhost:8001.

Requires requirements-ui.txt and Chromium installed in .browser-cache.
Creates random test-only accounts, never accesses the demo database.
"""
from pathlib import Path
import json
import os
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".browser-cache"))

from playwright.sync_api import sync_playwright


def main():
    suffix = secrets.token_hex(6)
    password = secrets.token_urlsafe(24)
    accounts = {role: f"ui-{role}-{suffix}" for role in ("admin", "staff")}
    payload = json.dumps({"accounts": accounts, "password": password})
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
        user = User(username=username, email=username+'@example.invalid', role=role, full_name='Quản trị TechFlow' if role=='admin' else 'Nhân viên TechFlow')
        user.set_password(data['password'])
        db.session.add(user)
    db.session.commit()
print('Isolated UI accounts ready; credentials not printed.')
""".replace("PAYLOAD", repr(payload))
    subprocess.run(["docker", "compose", "-f", "docker-compose.db-test.yml", "exec", "-T", "ui", "python", "-"],
                   cwd=ROOT, input=source, text=True, encoding="utf-8", check=True)
    screenshots = ROOT / "docs" / "screenshots"
    screenshots.mkdir(exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for label, width, height in [("desktop", 1440, 1000), ("tablet", 834, 1112), ("mobile", 390, 844)]:
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            response = page.goto("http://localhost:8001/login")
            assert response.status == 200
            page.evaluate("document.fonts.ready")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(screenshots / f"stage3-login-{label}.png"), full_page=True)
            page.locator("#identity").fill(accounts["admin"])
            page.locator("#password").fill(password)
            page.get_by_role("button", name="Hiện mật khẩu").click()
            assert page.locator("#password").get_attribute("type") == "text"
            page.get_by_role("button", name="Ẩn mật khẩu").click()
            page.get_by_role("button", name="Đăng nhập", exact=True).click()
            page.wait_for_url("**/dashboard")
            assert page.get_by_role("heading", name="Tổng quan", exact=True).is_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(screenshots / f"stage3-dashboard-{label}.png"), full_page=True)
            if width < 992:
                page.get_by_role("button", name="Mở menu điều hướng").click()
                page.wait_for_selector("#admin-sidebar.show", state="visible")
                assert page.get_by_role("link", name="Không gian quản trị").is_visible()
                page.screenshot(path=str(screenshots / f"stage3-menu-{label}.png"), full_page=True)
                page.get_by_role("button", name="Đóng menu").click()
                page.wait_for_selector("#admin-sidebar:not(.show)", state="attached")
            # A real protected admin page and friendly error state.
            assert page.goto("http://localhost:8001/admin").status == 200
            assert page.goto("http://localhost:8001/missing-ui-page").status == 404
            page.get_by_role("button", name="Đăng xuất", exact=True).click()
            page.wait_for_url("**/login")
            assert page.goto("http://localhost:8001/dashboard").url.startswith("http://localhost:8001/login")
            context.close()
            print(f"Browser {label} {width}x{height}: login, dashboard, menu, logout and overflow checks passed.")
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.goto("http://localhost:8001/login")
        page.locator("#identity").fill(accounts["staff"] + "@example.invalid")
        page.locator("#password").fill(password)
        page.get_by_role("button", name="Đăng nhập", exact=True).click()
        page.wait_for_url("**/dashboard")
        assert page.get_by_role("link", name="Không gian quản trị").count() == 0
        assert page.goto("http://localhost:8001/admin").status == 403
        page.screenshot(path=str(screenshots / "stage3-staff-403.png"), full_page=True)
        context.close()
        browser.close()
    assert not errors, "Browser JavaScript error detected"
    print('Browser verification passed; screenshots saved in docs/screenshots. No demo data changed.')


if __name__ == "__main__":
    main()
