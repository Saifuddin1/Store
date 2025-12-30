from functools import wraps
from flask_login import current_user
from flask import abort, redirect, url_for

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped