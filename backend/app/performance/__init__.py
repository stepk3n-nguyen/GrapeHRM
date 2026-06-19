from flask import Blueprint

performance_bp = Blueprint("performance", __name__, url_prefix="/api")

from app.performance import routes  # noqa: E402,F401
