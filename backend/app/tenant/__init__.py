from flask import Blueprint

tenant_bp = Blueprint("tenant", __name__, url_prefix="/api/tenants")

from app.tenant import routes  # noqa: E402,F401
