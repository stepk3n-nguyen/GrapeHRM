"""
Application Factory — điểm khởi tạo toàn bộ ứng dụng Flask.
Hàm create_app() tạo Flask app, nạp config, khởi tạo extensions,
đăng ký blueprints và middleware.
"""

import os

from flask import Flask

from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors, ma


def create_app(config_name: str = None) -> Flask:
    """
    Tạo và cấu hình Flask app.

    Args:
        config_name: Tên môi trường ("development", "production", "testing").
                     Mặc định đọc từ biến FLASK_ENV.
    Returns:
        Flask app đã cấu hình đầy đủ.
    """

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)

    # ── Nạp cấu hình theo môi trường ────────────────────────────────
    app.config.from_object(config_by_name[config_name])

    # ── Khởi tạo extensions (gắn vào app) ───────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    ma.init_app(app)

    # ── Import models để Flask-Migrate phát hiện bảng ────────────────
    with app.app_context():
        from app import models  # noqa: F401 — cần import để Alembic detect

        # Tự động tạo bảng nếu chưa tồn tại (dev mode)
        db.create_all()

        # Seed dữ liệu ban đầu (tenant + admin user)
        from app.seed import seed_initial_data
        seed_initial_data()

    # ── Đăng ký middleware multi-tenant ──────────────────────────────
    from app.middleware.tenant_filter import tenant_filter_middleware
    tenant_filter_middleware(app)

    # ── Đăng ký blueprints ──────────────────────────────────────────
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.employee.routes import employee_bp, title_bp, department_bp
    app.register_blueprint(employee_bp)
    app.register_blueprint(title_bp)
    app.register_blueprint(department_bp)

    from app.leave.routes import (
        leave_type_bp, leave_policy_bp, leave_request_bp,
        leave_balance_bp, attendance_bp
    )
    app.register_blueprint(leave_type_bp)
    app.register_blueprint(leave_policy_bp)
    app.register_blueprint(leave_request_bp)
    app.register_blueprint(leave_balance_bp)
    app.register_blueprint(attendance_bp)

    # ── Route kiểm tra sức khỏe (health check) ──────────────────────
    @app.route("/api/health")
    def health():
        return {"status": "ok", "service": "GrapeHRM API"}

    return app
