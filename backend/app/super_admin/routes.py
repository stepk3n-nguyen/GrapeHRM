"""
Super Admin — quản lý các tenant (chỉ role super_admin). Truy cập cross-tenant.
"""

from functools import wraps

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.employee import Employee
from app.models.tenant_config import TenantConfig
from app.services.tenant_service import create_tenant_with_admin
from . import super_admin_bp


def super_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "super_admin":
            return jsonify({"error": "Chỉ Super Admin mới có quyền"}), 403
        return fn(*args, **kwargs)
    return wrapper


def _tenant_summary(t):
    cfg = TenantConfig.query.filter_by(tenant_id=t.id).first()
    return {
        "id": t.id, "name": t.name, "slug": t.slug, "is_active": t.is_active,
        "plan": cfg.plan if cfg else "FREE",
        "max_employees": cfg.max_employees if cfg else 50,
        "total_employees": Employee.query.filter_by(tenant_id=t.id).count(),
        "total_users": User.query.filter_by(tenant_id=t.id).count(),
        "created_at": t.created_at.isoformat() if getattr(t, "created_at", None) else None,
    }


@super_admin_bp.route("/tenants", methods=["GET"])
@jwt_required()
@super_admin_required
def list_tenants():
    tenants = Tenant.query.order_by(Tenant.id).all()
    return jsonify({"items": [_tenant_summary(t) for t in tenants], "total": len(tenants)}), 200


@super_admin_bp.route("/tenants/<int:tid>", methods=["GET"])
@jwt_required()
@super_admin_required
def get_tenant(tid):
    t = Tenant.query.get(tid)
    if not t:
        return jsonify({"error": "Không tìm thấy"}), 404
    return jsonify(_tenant_summary(t)), 200


@super_admin_bp.route("/tenants", methods=["POST"])
@jwt_required()
@super_admin_required
def create_tenant():
    d = request.get_json(silent=True) or {}
    tenant, err = create_tenant_with_admin(
        organization_name=d.get("organization_name"), slug=d.get("slug"),
        admin_username=d.get("admin_username"), admin_email=d.get("admin_email"),
        admin_password=d.get("admin_password"), country=d.get("country"), city=d.get("city"),
    )
    if err:
        return jsonify({"error": err}), 409 if "đã được sử dụng" in err else 400
    return jsonify({"message": "Đã tạo tổ chức", "tenant": _tenant_summary(tenant)}), 201


@super_admin_bp.route("/tenants/<int:tid>", methods=["PUT"])
@jwt_required()
@super_admin_required
def update_tenant(tid):
    t = Tenant.query.get(tid)
    if not t:
        return jsonify({"error": "Không tìm thấy"}), 404
    d = request.get_json(silent=True) or {}
    for f in ["name", "phone", "email", "country", "city", "address"]:
        if f in d:
            setattr(t, f, d[f])
    # kiểm tra tenant đã có bảng cấu hình TenantConfig chưa, nếu ko thì tạo mới 
    cfg = TenantConfig.query.filter_by(tenant_id=t.id).first()
    if not cfg:
        cfg = TenantConfig(tenant_id=t.id)
        db.session.add(cfg)
    if "plan" in d:
        cfg.plan = d["plan"]
    if "max_employees" in d:
        cfg.max_employees = d["max_employees"]

    db.session.commit()
    return jsonify({"message": "Đã cập nhật tổ chức"}), 200


@super_admin_bp.route("/tenants/<int:tid>/toggle-active", methods=["PUT"])
@jwt_required()
@super_admin_required
def toggle_tenant(tid):
    t = Tenant.query.get(tid)
    if not t:
        return jsonify({"error": "Không tìm thấy"}), 404
    t.is_active = not t.is_active
    db.session.commit()
    return jsonify({"message": "Đã cập nhật", "is_active": t.is_active}), 200


@super_admin_bp.route("/tenants/<int:tid>", methods=["DELETE"])
@jwt_required()
@super_admin_required
def delete_tenant(tid):
    """Soft delete — vô hiệu hóa tenant (an toàn hơn xóa cứng)."""
    t = Tenant.query.get(tid)
    if not t:
        return jsonify({"error": "Không tìm thấy"}), 404
    t.is_active = False
    db.session.commit()
    return jsonify({"message": "Đã vô hiệu hóa tổ chức"}), 200
