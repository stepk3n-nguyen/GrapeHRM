"""
Khởi tạo các extension dùng chung trong toàn bộ ứng dụng Flask.
Các extension được tạo ở đây nhưng chưa gắn vào app — việc gắn (init_app)
sẽ thực hiện trong create_app() tại __init__.py.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow

# ORM — quản lý kết nối database và model
db = SQLAlchemy()

# Migration — quản lý thay đổi cấu trúc bảng (giống Alembic)
migrate = Migrate()

# JWT — xác thực người dùng bằng JSON Web Token
jwt = JWTManager()

# CORS — cho phép frontend (port 3000) gọi API (port 5000)
cors = CORS()

# Marshmallow — serialize/deserialize dữ liệu (model ↔ JSON)
ma = Marshmallow()
