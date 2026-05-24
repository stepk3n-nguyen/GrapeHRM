"""
Middleware cách ly dữ liệu multi-tenant.
Chạy trước mỗi request (trừ auth endpoints) để:
1. Đọc tenant_id từ JWT claims.
2. Gắn vào Flask g object để các route/query dùng chung.
"""

from flask import g, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError


# Danh sách các URL prefix không cần xác thực tenant
PUBLIC_PREFIXES = ("/api/auth/login", "/api/auth/refresh", "/api/health")


def tenant_filter_middleware(app):
    """
    Đăng ký before_request hook — tự động inject g.tenant_id
    từ JWT token cho mọi request cần xác thực.
    """

    @app.before_request
    def extract_tenant_from_jwt():
        # Bỏ qua các endpoint công khai (login, refresh)
        if any(request.path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            return None

        # Bỏ qua nếu không phải API request
        if not request.path.startswith("/api"):
            return None

        try:
            # Xác minh JWT token hợp lệ
            verify_jwt_in_request()
            claims = get_jwt()

            # Lấy tenant_id từ custom claims trong token
            g.tenant_id = claims.get("tenant_id")
            g.user_id = claims.get("sub")  # subject = user id
            g.user_role = claims.get("role")

            if g.tenant_id is None:
                from flask import jsonify
                return jsonify({"error": "Thiếu thông tin tenant trong token"}), 403

        except NoAuthorizationError:
            from flask import jsonify
            return jsonify({"error": "Yêu cầu đăng nhập để truy cập"}), 401

    return app
