from flask import Blueprint

super_admin_bp = Blueprint("super_admin", __name__, url_prefix="/api/super-admin")

from app.super_admin import routes  # noqa: E402,F401
