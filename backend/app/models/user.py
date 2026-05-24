"""
Model User — tài khoản đăng nhập hệ thống.
Tách riêng khỏi Employee: super_admin có thể không phải nhân viên.
"""

import bcrypt

from app.extensions import db
from app.models.base import TenantMixin


class User(TenantMixin, db.Model):
    """Bảng users — xác thực và phân quyền."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Liên kết tới nhân viên (nullable — super_admin có thể không cần hồ sơ nhân viên)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)

    # Thông tin đăng nhập
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Vai trò trong hệ thống — quyết định quyền truy cập
    role = db.Column(
        db.Enum(
            "super_admin", "admin", "hr_manager", "supervisor", "employee",
            name="user_role_enum",
        ),
        default="employee",
    )

    # Trạng thái tài khoản — False = bị khóa
    is_active = db.Column(db.Boolean, default=True)

    # Thời điểm đăng nhập gần nhất
    last_login = db.Column(db.DateTime, nullable=True)

    # Thời điểm tạo tài khoản
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Ràng buộc: username phải duy nhất trong cùng 1 tenant
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "username", name="uq_tenant_username"),
    )

    # ── Phương thức xử lý mật khẩu ──────────────────────────────────

    def set_password(self, plain_password: str) -> None:
        """Mã hóa mật khẩu bằng bcrypt rồi lưu vào password_hash."""
        hashed = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(),
        )
        self.password_hash = hashed.decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        """So sánh mật khẩu người dùng nhập với hash đã lưu."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    def __repr__(self):
        return f"<User {self.username}>"
