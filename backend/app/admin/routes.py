from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from dotenv import set_key
import os

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
