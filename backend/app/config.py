"""
Cấu hình ứng dụng Flask.
Mỗi class tương ứng với một môi trường (development, production, testing).
"""

import os


class Config:
    """Cấu hình chung — các giá trị dùng cho mọi môi trường."""

    # Khóa bí mật cho JWT token, đọc từ biến môi trường
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")

    # Thời gian sống của access token (phút)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 30))  # 30 phút

    # Thời gian sống của refresh token (ngày)
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 7))  # 7 ngày

    # Chuỗi kết nối database — PyMySQL driver cho MySQL 8
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/grapehrm"
    )

    # Tắt tính năng theo dõi thay đổi model (tốn bộ nhớ, không cần thiết)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Bật chế độ debug theo biến môi trường
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"


class DevelopmentConfig(Config):
    """Cấu hình riêng cho môi trường phát triển."""

    DEBUG = True

    # Hiển thị câu lệnh SQL trong console (hỗ trợ debug query)
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Cấu hình riêng cho môi trường production."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Cấu hình riêng cho chạy test — dùng database SQLite in-memory."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False


# Ánh xạ tên môi trường → class cấu hình tương ứng
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
