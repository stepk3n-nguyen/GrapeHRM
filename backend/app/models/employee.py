"""
Model Employee — hồ sơ nhân viên chính.
Đây là model lớn nhất trong hệ thống, chứa toàn bộ thông tin cá nhân,
liên hệ và công việc của nhân viên. Phase 1 chỉ tạo các cột cơ bản.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class Employee(TenantMixin, TimestampMixin, db.Model):
    """Bảng employees — hồ sơ nhân sự."""

    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Mã nhân viên tùy chỉnh (vd: "NV-001") — hiển thị trên thẻ, bảng lương
    employee_id = db.Column(db.String(50), nullable=True)

    # ── Thông tin cá nhân ────────────────────────────────────────────

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    # Giới tính: 1 = Nam, 2 = Nữ, 3 = Khác
    gender = db.Column(db.SmallInteger, nullable=True)

    marital_status = db.Column(db.String(20), nullable=True)
    birthday = db.Column(db.Date, nullable=True)

    # ── Thông tin liên hệ ────────────────────────────────────────────

    mobile = db.Column(db.String(50), nullable=True)
    work_email = db.Column(db.String(100), nullable=True)

    # ── Thông tin công việc ──────────────────────────────────────────

    joined_date = db.Column(db.Date, nullable=True)

    # Trạng thái nhân viên: đang làm việc hay đã nghỉ
    state = db.Column(
        db.Enum("ACTIVE", "TERMINATED", name="employee_state_enum"),
        default="ACTIVE",
    )

    # Ảnh đại diện
    profile_pic_url = db.Column(db.Text, nullable=True)

    # Vị trí công việc (Job Position)
    position_id = db.Column(
        db.Integer,
        db.ForeignKey("job_positions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Quan hệ với User (1 Employee ↔ 1 User account) ──────────────

    user = db.relationship("User", backref="employee", uselist=False,
                           foreign_keys="User.employee_id")

    def full_name(self) -> str:
        """Trả về họ tên đầy đủ."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p)

    def __repr__(self):
        return f"<Employee {self.full_name()} serial={self.serial}>"


class EmployeeSequence(db.Model):
    """Bảng lưu số thứ tự tăng dần để tự động tạo mã nhân sự (employee_id) cho từng tenant."""

    __tablename__ = "employee_sequences"

    tenant_id = db.Column(db.Integer, primary_key=True)
    current_value = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<EmployeeSequence tenant={self.tenant_id} val={self.current_value}>"


class JobPosition(TenantMixin, TimestampMixin, db.Model):
    """Bảng job_positions — danh sách chức vụ/vị trí công việc."""

    __tablename__ = "job_positions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # Quan hệ ngược lại (1 Position -> nhiều Employees)
    employees = db.relationship("Employee", backref="position", lazy=True)

    def __repr__(self):
        return f"<JobPosition {self.name} tenant={self.tenant_id}>"
