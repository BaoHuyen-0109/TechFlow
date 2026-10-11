from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*roles):
    def decorate(view):
        @wraps(view)
        @login_required
        def protected(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return protected
    return decorate


admin_required = role_required("admin")
business_required = role_required("admin", "staff")
client_required = role_required("client")
