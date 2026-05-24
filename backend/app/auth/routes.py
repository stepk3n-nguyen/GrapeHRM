"""
Blueprint Auth — xử lý đăng nhập, làm mới token và lấy thông tin user.
Endpoints:
    POST /api/auth/login    — đăng nhập, trả access + refresh token
    POST /api/auth/refresh  — dùng refresh token để lấy access token mới
    GET  /api/auth/me       — trả thông tin user đang đăng nhập
"""

from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

from app.extensions import db
from app.models.user import User

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

    if not username or not password:
        return jsonify({"error": "Vui lòng nhập username và password"}), 400

    # Tìm user theo username (tất cả tenant — vì chưa biết tenant nào)
    user = User.query.filter_by(username=username, is_active=True).first()

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

    # Cập nhật thời điểm đăng nhập cuối
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message": "Đăng nhập thành công",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
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

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }), 200
