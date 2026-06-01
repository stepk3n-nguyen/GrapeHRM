"""
Model User — tài khoản đăng nhập hệ thống.
Tách riêng khỏi Employee: super_admin có thể không phải nhân viên.
"""

from werkzeug.security import generate_password_hash, check_password_hash

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
            "super_admin", "admin", "hr_manager", "employee",
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
        """Mã hóa mật khẩu bằng werkzeug.security rồi lưu vào password_hash."""
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """So sánh mật khẩu người dùng nhập với hash đã lưu."""
        # Fallback in case there are old bcrypt hashes
        if self.password_hash.startswith("$2b$"):
            # We would normally use bcrypt to verify, but since we removed it, 
            # we will just reset the admin password or handle it gracefully.
            # However, new seeds will use scrypt/pbkdf2 automatically.
            try:
                # pyrefly: ignore [missing-import]
                import bcrypt
                return bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    self.password_hash.encode("utf-8"),
                )
            except ImportError:
                return False
                
        return check_password_hash(self.password_hash, plain_password)

    def __repr__(self):
        return f"<User {self.username}>"
