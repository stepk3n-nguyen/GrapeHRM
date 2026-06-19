"""
Đăng ký tổ chức mới (public — không cần đăng nhập).
"""

from flask import request, jsonify

from app.services.tenant_service import create_tenant_with_admin
from . import tenant_bp


@tenant_bp.route("/register", methods=["POST"])
def register_tenant():
    d = request.get_json(silent=True) or {}
    tenant, err = create_tenant_with_admin(
        organization_name=d.get("organization_name"),
        slug=d.get("slug"),
        admin_username=d.get("admin_username"),
        admin_email=d.get("admin_email"),
        admin_password=d.get("admin_password"),
        country=d.get("country"),
        city=d.get("city"),
    )
    if err:
        status = 409 if "đã được sử dụng" in err else 400
        return jsonify({"error": err}), status

    return jsonify({
        "message": "Đăng ký tổ chức thành công",
        "tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug},
        "admin": {"username": d.get("admin_username"), "email": d.get("admin_email")},
    }), 201
