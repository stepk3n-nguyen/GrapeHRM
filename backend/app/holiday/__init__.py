from flask import Blueprint

holiday_bp = Blueprint("holiday", __name__, url_prefix="/api/holidays")

from app.holiday import routes  # noqa: E402,F401
