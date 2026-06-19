from flask import Blueprint

contract_bp = Blueprint("contract", __name__, url_prefix="/api/contracts")

from app.contract import routes  # noqa: E402,F401
