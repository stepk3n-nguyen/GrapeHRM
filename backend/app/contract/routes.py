"""
Blueprint Hợp đồng lao động (Admin/HR). Có cảnh báo HĐ sắp hết hạn.
"""

from datetime import datetime, date, timedelta

from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models.contract import Contract
from app.models.employee import Employee
from app.services.audit_service import log_action
from . import contract_bp

_TYPE_LABEL = {
    "PROBATION": "Thử việc", "FIXED_TERM": "Xác định thời hạn",
    "INDEFINITE": "Không xác định thời hạn", "SEASONAL": "Thời vụ",
}
EXPIRY_WARNING_DAYS = 30


def _guard():
    if get_jwt().get("role") not in ("super_admin", "admin", "hr_manager"):
        return jsonify({"error": "Không có quyền truy cập"}), 403
    return None


def _parse(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").date() if d else None
    except (ValueError, TypeError):
        return None


def _serialize(c):
    today = date.today()
    days_left = (c.end_date - today).days if c.end_date else None
    return {
        "id": c.id, "employee_id": c.employee_id,
        "employee_name": c.employee.full_name() if c.employee else "?",
        "employee_code": c.employee.employee_id if c.employee else None,
        "contract_number": c.contract_number,
        "contract_type": c.contract_type,
        "contract_type_label": _TYPE_LABEL.get(c.contract_type, c.contract_type),
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "basic_salary": float(c.basic_salary) if c.basic_salary is not None else None,
        "signed_date": c.signed_date.isoformat() if c.signed_date else None,
        "status": c.status,
        "days_left": days_left,
        "expiring_soon": days_left is not None and 0 <= days_left <= EXPIRY_WARNING_DAYS and c.status == "ACTIVE",
        "note": c.note,
    }


@contract_bp.route("", methods=["GET"])
@jwt_required()
def list_contracts():
    block = _guard()
    if block:
        return block
    q = Contract.query.filter_by(tenant_id=g.tenant_id)
    if request.args.get("employee_id"):
        q = q.filter_by(employee_id=request.args.get("employee_id", type=int))
    if request.args.get("expiring") == "1":
        soon = date.today() + timedelta(days=EXPIRY_WARNING_DAYS)
        q = q.filter(Contract.status == "ACTIVE", Contract.end_date.isnot(None),
                     Contract.end_date <= soon, Contract.end_date >= date.today())
    items = q.order_by(Contract.start_date.desc()).all()
    return jsonify([_serialize(c) for c in items]), 200


@contract_bp.route("", methods=["POST"])
@jwt_required()
def create_contract():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    emp_id = d.get("employee_id")
    start = _parse(d.get("start_date"))
    if not emp_id or not start:
        return jsonify({"error": "Thiếu nhân viên hoặc ngày bắt đầu"}), 400
    if not Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first():
        return jsonify({"error": "Nhân viên không hợp lệ"}), 400

    c = Contract(
        tenant_id=g.tenant_id, employee_id=emp_id,
        contract_number=d.get("contract_number"),
        contract_type=d.get("contract_type", "FIXED_TERM"),
        start_date=start, end_date=_parse(d.get("end_date")),
        basic_salary=d.get("basic_salary") or None,
        signed_date=_parse(d.get("signed_date")),
        status=d.get("status", "ACTIVE"), note=d.get("note"),
    )
    db.session.add(c)
    log_action("CREATE", "CONTRACT", details={"employee_id": emp_id})
    db.session.commit()
    return jsonify({"message": "Đã tạo hợp đồng", "id": c.id}), 201


@contract_bp.route("/<int:cid>", methods=["PUT"])
@jwt_required()
def update_contract(cid):
    block = _guard()
    if block:
        return block
    c = Contract.query.filter_by(id=cid, tenant_id=g.tenant_id).first()
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    d = request.get_json(silent=True) or {}
    for f in ("contract_number", "contract_type", "status", "note"):
        if f in d:
            setattr(c, f, d[f])
    for f in ("start_date", "end_date", "signed_date"):
        if f in d:
            setattr(c, f, _parse(d[f]))
    if "basic_salary" in d:
        c.basic_salary = d["basic_salary"] or None
    db.session.commit()
    return jsonify({"message": "Đã cập nhật"}), 200


@contract_bp.route("/<int:cid>", methods=["DELETE"])
@jwt_required()
def delete_contract(cid):
    block = _guard()
    if block:
        return block
    c = Contract.query.filter_by(id=cid, tenant_id=g.tenant_id).first()
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200
