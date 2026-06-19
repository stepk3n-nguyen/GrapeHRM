from flask import Blueprint

compensation_bp = Blueprint("compensation", __name__, url_prefix="/api")

from app.compensation import routes  # noqa: E402,F401
