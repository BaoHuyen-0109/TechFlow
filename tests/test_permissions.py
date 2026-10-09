import pytest
from flask_login import UserMixin, login_user
from werkzeug.exceptions import Forbidden

from app.auth.permissions import admin_required, business_required


class SessionUser(UserMixin):
    id = "unit-user"

    def __init__(self, role):
        self.role = role


@pytest.mark.parametrize("decorator, role, allowed", [
    (admin_required, "admin", True),
    (admin_required, "staff", False),
    (admin_required, "unknown", False),
    (business_required, "admin", True),
    (business_required, "staff", True),
    (business_required, "unknown", False),
])
def test_role_policy(app, decorator, role, allowed):
    with app.test_request_context():
        login_user(SessionUser(role))
        view = decorator(lambda: "authorized")
        if allowed:
            assert view() == "authorized"
        else:
            with pytest.raises(Forbidden):
                view()


@pytest.mark.parametrize("decorator", [admin_required, business_required])
def test_role_policy_requires_login(app, decorator):
    with app.test_request_context():
        response = decorator(lambda: "authorized")()
        assert response.status_code == 302 and response.location.startswith("/login?")
