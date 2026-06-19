from flask import Blueprint

recruitment_bp = Blueprint("recruitment", __name__, url_prefix="/api")

from app.recruitment import routes  # noqa: E402,F401
