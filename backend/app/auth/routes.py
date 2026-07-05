"""
Blueprint Auth — xử lý đăng nhập, làm mới token và lấy thông tin user.
Endpoints:
    POST /api/auth/login    — đăng nhập, trả access + refresh token
    POST /api/auth/refresh  — dùng refresh token để lấy access token mới
    GET  /api/auth/me       — trả thông tin user đang đăng nhập
"""

import re
from datetime import datetime, timezone, timedelta

# pyrefly: ignore [missing-import]
from flask import Blueprint, request, jsonify, current_app
# pyrefly: ignore [missing-import]
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

from app.extensions import db
from app.models.user import User
from app.models.tenant import Tenant

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Đăng nhập bằng username + password.
    Trả về access_token và refresh_token nếu thành công.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Thiếu dữ liệu đăng nhập"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")
    tenant_slug = data.get("tenant_slug", "").strip().lower()

    if not username or not password:
        return jsonify({"error": "Vui lòng nhập username và password"}), 400

    if not tenant_slug:
        return jsonify({"error": "Vui lòng nhập mã tổ chức"}), 400

    # Xác định tổ chức theo slug TRƯỚC khi tìm user — tránh trùng username
    # giữa các tenant (2 công ty cùng có tài khoản "admin").
    tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
    if tenant is None:
        return jsonify({"error": "Tổ chức không tồn tại hoặc đã bị vô hiệu hóa"}), 404

    # Tìm user trong đúng tenant đã xác định
    user = User.query.filter_by(
        username=username, tenant_id=tenant.id, is_active=True
    ).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": "Sai tên đăng nhập hoặc mật khẩu"}), 401

    # Tạo custom claims chứa tenant_id và role — middleware sẽ đọc claims này
    additional_claims = {
        "tenant_id": user.tenant_id,
        "role": user.role,
        "username": user.username,
    }

    # Đọc thời gian hết hạn từ config
    access_expires = timedelta(
        minutes=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 30)
    )
    refresh_expires = timedelta(
        days=current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES", 7)
    )

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims,
        expires_delta=access_expires,
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims=additional_claims,
        expires_delta=refresh_expires,
    )

    # Cập nhật thời điểm đăng nhập cuối + ghi nhật ký
    user.last_login = datetime.now(timezone.utc)
    from app.services.audit_service import log_action
    log_action("LOGIN", "USER", user.id, tenant_id=user.tenant_id, user_id=user.id)
    db.session.commit()

    employee_full_name = None
    employee_code = None
    if user.employee:
        employee_full_name = user.employee.full_name()
        employee_code = user.employee.employee_id

    return jsonify({
        "message": "Đăng nhập thành công",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "employee_id": user.employee_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "employee_full_name": employee_full_name,
            "employee_code": employee_code,
        },
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Dùng refresh_token để lấy access_token mới.
    Client gửi refresh_token trong header Authorization.
    """
    current_user_id = get_jwt_identity()
    claims = get_jwt()

    # Giữ nguyên claims từ token cũ
    additional_claims = {
        "tenant_id": claims.get("tenant_id"),
        "role": claims.get("role"),
        "username": claims.get("username"),
    }

    access_expires = timedelta(
        minutes=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 30)
    )

    new_access_token = create_access_token(
        identity=current_user_id,
        additional_claims=additional_claims,
        expires_delta=access_expires,
    )

    return jsonify({"access_token": new_access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Trả thông tin user đang đăng nhập.
    Frontend gọi endpoint này sau khi load trang để kiểm tra phiên đăng nhập.
    """
    current_user_id = get_jwt_identity()

    user = User.query.get(int(current_user_id))

    if user is None:
        return jsonify({"error": "Không tìm thấy tài khoản"}), 404

    employee_full_name = None
    employee_code = None
    if user.employee:
        employee_full_name = user.employee.full_name()
        employee_code = user.employee.employee_id

    return jsonify({
        "id": user.id,
        "employee_id": user.employee_id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "employee_full_name": employee_full_name,
        "employee_code": employee_code,
    }), 200


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """Đổi mật khẩu cho chính user đang đăng nhập."""
    user = User.query.get(int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "Không tìm thấy tài khoản"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Thiếu dữ liệu"}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    # Xác thực mật khẩu hiện tại
    if not user.check_password(current_password):
        return jsonify({"error": "Mật khẩu hiện tại không đúng"}), 401

    # Kiểm tra khớp xác nhận
    if new_password != confirm_password:
        return jsonify({"error": "Mật khẩu xác nhận không khớp"}), 400

    # Không cho trùng mật khẩu cũ
    if current_password == new_password:
        return jsonify({"error": "Mật khẩu mới không được trùng với mật khẩu cũ"}), 400

    # Kiểm tra độ mạnh: tối thiểu 8 ký tự, có chữ hoa, chữ thường và số
    if len(new_password) < 8:
        return jsonify({"error": "Mật khẩu mới phải có ít nhất 8 ký tự"}), 400
    if not re.search(r"[A-Z]", new_password):
        return jsonify({"error": "Mật khẩu mới phải chứa ít nhất 1 chữ hoa"}), 400
    if not re.search(r"[a-z]", new_password):
        return jsonify({"error": "Mật khẩu mới phải chứa ít nhất 1 chữ thường"}), 400
    if not re.search(r"[0-9]", new_password):
        return jsonify({"error": "Mật khẩu mới phải chứa ít nhất 1 chữ số"}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Đổi mật khẩu thành công"}), 200
