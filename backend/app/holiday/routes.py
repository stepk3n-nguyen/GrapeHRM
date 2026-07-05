"""
Blueprint Holiday — quản lý lịch ngày lễ của tenant (Admin/HR).
Ngày lễ được loại trừ khỏi ngày công chuẩn (lương) và số ngày trừ quỹ phép.
"""

from datetime import date, datetime

from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.holiday import Holiday
from app.services.audit_service import log_action
from app.services.vn_holidays import seed_vn_holidays_for_tenant
from . import holiday_bp


def _is_hr_admin():
    return get_jwt().get("role") in ["super_admin", "admin", "hr_manager"]


def _guard():
    if not _is_hr_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
    return None


def _serialize(h):
    return {
        "id": h.id,
        "name": h.name,
        "date": h.date.isoformat(),
        "is_paid": h.is_paid,
        "is_recurring": h.is_recurring,
    }


@holiday_bp.route("", methods=["GET"])
@jwt_required()
def list_holidays():
    """Danh sách ngày lễ; lọc theo ?year=YYYY (mặc định năm hiện tại)."""
    year = request.args.get("year", type=int)
    q = Holiday.query.filter_by(tenant_id=g.tenant_id)
    if year:
        q = q.filter(extract("year", Holiday.date) == year)
    items = q.order_by(Holiday.date.asc()).all()
    return jsonify([_serialize(h) for h in items]), 200


@holiday_bp.route("", methods=["POST"])
@jwt_required()
def create_holiday():
    block = _guard()
    if block:
        return block
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    raw_date = data.get("date")
    if not name or not raw_date:
        return jsonify({"error": "Thiếu tên hoặc ngày"}), 400
    try:
        d = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"error": "Ngày không hợp lệ (định dạng YYYY-MM-DD)"}), 400

    h = Holiday(
        tenant_id=g.tenant_id, name=name, date=d,
        is_paid=bool(data.get("is_paid", True)),
        is_recurring=bool(data.get("is_recurring", False)),
    )
    db.session.add(h)
    try:
        log_action("CREATE", "HOLIDAY", details={"name": name, "date": raw_date})
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ngày này đã có trong lịch lễ"}), 409
    return jsonify({"message": "Đã thêm ngày lễ", "id": h.id}), 201


@holiday_bp.route("/<int:hid>", methods=["PUT"])
@jwt_required()
def update_holiday(hid):
    block = _guard()
    if block:
        return block
    h = Holiday.query.filter_by(id=hid, tenant_id=g.tenant_id).first()
    if not h:
        return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}
    if "name" in data:
        h.name = (data["name"] or "").strip() or h.name
    if "date" in data:
        try:
            h.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return jsonify({"error": "Ngày không hợp lệ"}), 400
    if "is_paid" in data:
        h.is_paid = bool(data["is_paid"])
    if "is_recurring" in data:
        h.is_recurring = bool(data["is_recurring"])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Trùng ngày với một ngày lễ khác"}), 409
    return jsonify({"message": "Cập nhật thành công"}), 200


@holiday_bp.route("/<int:hid>", methods=["DELETE"])
@jwt_required()
def delete_holiday(hid):
    block = _guard()
    if block:
        return block
    h = Holiday.query.filter_by(id=hid, tenant_id=g.tenant_id).first()
    if not h:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(h)
    log_action("DELETE", "HOLIDAY", resource_id=hid, details={"name": h.name})
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


@holiday_bp.route("/seed-vn", methods=["POST"])
@jwt_required()
def seed_vn_holidays():
    """Nạp nhanh lễ pháp định VN cho riêng tổ chức này. Bỏ qua ngày đã tồn tại.
    Admin có thể thêm/bớt/xóa sau cho khớp lịch nghỉ thực tế của công ty."""
    block = _guard()
    if block:
        return block
    data = request.get_json(silent=True) or {}
    year = int(data.get("year") or date.today().year)

    added, has_lunar = seed_vn_holidays_for_tenant(g.tenant_id, year)
    log_action("CREATE", "HOLIDAY", details={"seed_vn": year, "added": added})
    db.session.commit()

    note = "" if has_lunar else " (Tết/Giỗ tổ năm này cần nhập tay vì theo lịch âm)"
    return jsonify({"message": f"Đã thêm {added} ngày lễ năm {year}{note}", "added": added}), 200
