from flask import request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from dotenv import set_key
import os

from app.extensions import db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.tenant_config import TenantConfig
from app.services.crypto_service import encrypt_secret
from . import admin_bp

def is_admin():
    claims = get_jwt()
    role = claims.get("role")
    return role in ["admin", "super_admin"]

@admin_bp.route("/smtp-config", methods=["GET"])
@jwt_required()
def get_smtp_config():
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
        
    config = {
        "MAIL_SERVER": current_app.config.get("MAIL_SERVER"),
        "MAIL_PORT": current_app.config.get("MAIL_PORT"),
        "MAIL_USE_TLS": current_app.config.get("MAIL_USE_TLS"),
        "MAIL_USERNAME": current_app.config.get("MAIL_USERNAME"),
        # Không trả về password thực tế vì lý do bảo mật
        "MAIL_PASSWORD_SET": bool(current_app.config.get("MAIL_PASSWORD")),
        "MAIL_DEFAULT_SENDER": current_app.config.get("MAIL_DEFAULT_SENDER")
    }
    return jsonify({"status": "success", "data": config}), 200

@admin_bp.route("/smtp-config", methods=["PUT"])
@jwt_required()
def update_smtp_config():
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
        
    data = request.get_json()
    
    env_path = os.path.join(current_app.root_path, '..', '.env')
    
    if "MAIL_SERVER" in data:
        set_key(env_path, "MAIL_SERVER", data["MAIL_SERVER"])
        current_app.config["MAIL_SERVER"] = data["MAIL_SERVER"]
        
    if "MAIL_PORT" in data:
        set_key(env_path, "MAIL_PORT", str(data["MAIL_PORT"]))
        current_app.config["MAIL_PORT"] = int(data["MAIL_PORT"])
        
    if "MAIL_USE_TLS" in data:
        set_key(env_path, "MAIL_USE_TLS", str(data["MAIL_USE_TLS"]))
        current_app.config["MAIL_USE_TLS"] = str(data["MAIL_USE_TLS"]).lower() in ["true", "1", "t"]
        
    if "MAIL_USERNAME" in data:
        set_key(env_path, "MAIL_USERNAME", data["MAIL_USERNAME"])
        current_app.config["MAIL_USERNAME"] = data["MAIL_USERNAME"]
        
    if "MAIL_PASSWORD" in data and data["MAIL_PASSWORD"]:
        set_key(env_path, "MAIL_PASSWORD", data["MAIL_PASSWORD"])
        current_app.config["MAIL_PASSWORD"] = data["MAIL_PASSWORD"]
        
    if "MAIL_DEFAULT_SENDER" in data:
        set_key(env_path, "MAIL_DEFAULT_SENDER", data["MAIL_DEFAULT_SENDER"])
        current_app.config["MAIL_DEFAULT_SENDER"] = data["MAIL_DEFAULT_SENDER"]

    return jsonify({"status": "success", "message": "Cập nhật cấu hình SMTP thành công"}), 200

@admin_bp.route("/smtp-test", methods=["POST"])
@jwt_required()
def test_smtp_config():
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
        
    data = request.get_json()
    recipient = data.get("email")
    if not recipient:
        return jsonify({"error": "Vui lòng cung cấp email người nhận"}), 400
        
    subject = "[GrapeHRM] Test SMTP Configuration ✅"
    body = """
    <html>
      <body style="font-family: Arial, sans-serif; color: #212529; line-height: 1.5; background-color: #F8F9FA; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #CED4DA; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1);">
          <div style="background-color: #0A6ED1; color: white; padding: 20px; text-align: center; font-size: 20px; font-weight: bold;">
            GrapeHRM Email Test
          </div>
          <div style="padding: 24px;">
            <p>Xin chào,</p>
            <p>Đây là email kiểm tra tính năng gửi thư qua SMTP từ hệ thống <strong>GrapeHRM</strong>.</p>
            <p>Việc cấu hình SMTP của bạn đã hoạt động thành công!</p>
          </div>
        </div>
      </body>
    </html>
    """
    
    from app.services.email_service import send_email
    send_email(current_app._get_current_object(), recipient, subject, body, is_html=True)

    return jsonify({"status": "success", "message": "Đã gửi yêu cầu test email"}), 200


# ── THÔNG TIN TỔ CHỨC (ORGANIZATION) ────────────────────────────────────

@admin_bp.route("/organization", methods=["GET"])
@jwt_required()
def get_organization():
    """Lấy thông tin tổ chức của tenant hiện tại."""
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

    tenant = Tenant.query.get(g.tenant_id)
    if not tenant:
        return jsonify({"error": "Không tìm thấy tổ chức"}), 404

    return jsonify({
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "tax_id": tenant.tax_id,
        "reg_number": tenant.reg_number,
        "phone": tenant.phone,
        "email": tenant.email,
        "country": tenant.country,
        "city": tenant.city,
        "address": tenant.address,
        "logo_url": tenant.logo_url,
    }), 200


@admin_bp.route("/organization", methods=["PUT"])
@jwt_required()
def update_organization():
    """Cập nhật thông tin tổ chức. KHÔNG cho đổi slug vì ảnh hưởng đăng nhập."""
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

    tenant = Tenant.query.get(g.tenant_id)
    if not tenant:
        return jsonify({"error": "Không tìm thấy tổ chức"}), 404

    data = request.get_json(silent=True) or {}
    editable = ["name", "tax_id", "reg_number", "phone", "email",
                "country", "city", "address", "logo_url"]
    for field in editable:
        if field in data:
            setattr(tenant, field, data[field])

    db.session.commit()
    return jsonify({"message": "Cập nhật thông tin tổ chức thành công"}), 200


# ── QUẢN LÝ TÀI KHOẢN NGƯỜI DÙNG (USER MANAGEMENT) ──────────────────────

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """Danh sách tài khoản trong tenant hiện tại."""
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

    users = User.query.filter_by(tenant_id=g.tenant_id).all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "employee_name": u.employee.full_name() if u.employee else None,
        "last_login": u.last_login.isoformat() if u.last_login else None,
    } for u in users]), 200


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["PUT"])
@jwt_required()
def toggle_user_active(user_id):
    """Khóa / Mở khóa một tài khoản."""
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

    if user_id == int(get_jwt_identity()):
        return jsonify({"error": "Không thể tự khóa tài khoản của chính mình"}), 400

    u = User.query.filter_by(id=user_id, tenant_id=g.tenant_id).first()
    if not u:
        return jsonify({"error": "Không tìm thấy tài khoản"}), 404

    u.is_active = not u.is_active
    db.session.commit()
    state = "mở khóa" if u.is_active else "khóa"
    return jsonify({"message": f"Đã {state} tài khoản", "is_active": u.is_active}), 200


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["PUT"])
@jwt_required()
def reset_user_password(user_id):
    """Reset mật khẩu tài khoản về mặc định '123456'."""
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

    u = User.query.filter_by(id=user_id, tenant_id=g.tenant_id).first()
    if not u:
        return jsonify({"error": "Không tìm thấy tài khoản"}), 404

    u.set_password("123456")
    db.session.commit()
    return jsonify({"message": "Đã reset mật khẩu về '123456'"}), 200


# ── NHẬT KÝ HOẠT ĐỘNG (AUDIT LOG) ───────────────────────────────────────
@admin_bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def list_audit_logs():
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(int(request.args.get("per_page", 50)), 100)

    q = AuditLog.query.filter_by(tenant_id=g.tenant_id)
    action = request.args.get("action")
    if action:
        q = q.filter_by(action=action)
    rtype = request.args.get("resource_type")
    if rtype:
        q = q.filter_by(resource_type=rtype)
    q = q.order_by(AuditLog.created_at.desc())

    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        "items": [{
            "id": l.id,
            "user_name": l.user.username if l.user else "Hệ thống",
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        } for l in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }), 200


# ── CẤU HÌNH SMTP RIÊNG CHO TENANT ──────────────────────────────────────
@admin_bp.route("/tenant-config", methods=["GET"])
@jwt_required()
def get_tenant_config():
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
    tc = TenantConfig.query.filter_by(tenant_id=g.tenant_id).first()
    if not tc:
        return jsonify({
            "mail_server": None, "mail_port": None, "mail_use_tls": True,
            "mail_username": None, "mail_password_set": False,
            "mail_default_sender": None, "plan": "FREE", "max_employees": 50,
        }), 200
    return jsonify({
        "mail_server": tc.mail_server, "mail_port": tc.mail_port,
        "mail_use_tls": tc.mail_use_tls, "mail_username": tc.mail_username,
        "mail_password_set": bool(tc.mail_password_encrypted),
        "mail_default_sender": tc.mail_default_sender,
        "plan": tc.plan, "max_employees": tc.max_employees,
    }), 200


@admin_bp.route("/tenant-config", methods=["PUT"])
@jwt_required()
def update_tenant_config():
    if not is_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
    tc = TenantConfig.query.filter_by(tenant_id=g.tenant_id).first()
    if not tc:
        tc = TenantConfig(tenant_id=g.tenant_id)
        db.session.add(tc)

    data = request.get_json(silent=True) or {}
    for f in ["mail_server", "mail_port", "mail_use_tls", "mail_username", "mail_default_sender"]:
        if f in data:
            setattr(tc, f, data[f])
    # Mã hóa mật khẩu SMTP nếu được gửi lên (không lưu plaintext)
    if data.get("mail_password"):
        tc.mail_password_encrypted = encrypt_secret(data["mail_password"])

    db.session.commit()
    return jsonify({"message": "Đã cập nhật cấu hình SMTP của tổ chức"}), 200
