"""
Models nghiệp vụ Tiền lương (Compensation).
Cấu trúc lương, phụ cấp, khấu trừ, mức lương nhân viên, đợt chạy lương, phiếu lương.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class SalaryStructure(TenantMixin, db.Model):
    __tablename__ = "salary_structures"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    basic_salary = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class SalaryAllowance(TenantMixin, db.Model):
    __tablename__ = "salary_allowances"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum("FIXED", "PERCENT", name="allowance_type"), nullable=False, default="FIXED")
    default_amount = db.Column(db.Numeric(12, 2), default=0)


class SalaryDeduction(TenantMixin, db.Model):
    __tablename__ = "salary_deductions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum("FIXED", "PERCENT", name="deduction_type"), nullable=False, default="PERCENT")
    default_amount = db.Column(db.Numeric(12, 2), default=0)


class EmployeeSalary(TenantMixin, db.Model):
    __tablename__ = "employee_salaries"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    structure_id = db.Column(db.Integer, db.ForeignKey("salary_structures.id", ondelete="SET NULL"), nullable=True)
    basic_salary = db.Column(db.Numeric(12, 2), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (db.UniqueConstraint("employee_id", "effective_date", name="uq_emp_effective"),)

    employee = db.relationship("Employee")
    structure = db.relationship("SalaryStructure")


class PayrollRun(TenantMixin, db.Model):
    __tablename__ = "payroll_runs"
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.SmallInteger, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum("DRAFT", "CONFIRMED", "LOCKED", name="payroll_status"), default="DRAFT")
    total_amount = db.Column(db.Numeric(14, 2), default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    confirmed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (db.UniqueConstraint("tenant_id", "month", "year", name="uq_tenant_month_year"),)

    payslips = db.relationship("Payslip", backref="payroll", cascade="all, delete-orphan")


class Payslip(db.Model):
    __tablename__ = "payslips"
    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    basic_salary = db.Column(db.Numeric(12, 2), nullable=False)
    total_work_days = db.Column(db.Numeric(4, 1), nullable=False)
    standard_work_days = db.Column(db.Integer, nullable=False, default=22)
    total_leave_days = db.Column(db.Numeric(4, 1), default=0)
    total_unpaid_leave = db.Column(db.Numeric(4, 1), default=0)
    total_allowances = db.Column(db.Numeric(12, 2), default=0)
    total_deductions = db.Column(db.Numeric(12, 2), default=0)   # BH bắt buộc (BHXH/BHYT/BHTN)

    # ── Tăng ca + thuế TNCN ─────────────────────────────────────────────
    overtime_hours = db.Column(db.Numeric(6, 1), default=0)
    overtime_pay = db.Column(db.Numeric(12, 2), default=0)
    gross_salary = db.Column(db.Numeric(12, 2), default=0)        # lương cơ bản pro-rated + phụ cấp + OT
    num_dependents = db.Column(db.Integer, default=0)
    taxable_income = db.Column(db.Numeric(12, 2), default=0)
    personal_income_tax = db.Column(db.Numeric(12, 2), default=0)

    net_salary = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    employee = db.relationship("Employee")
    items = db.relationship("PayslipItem", backref="payslip", cascade="all, delete-orphan")


class PayslipItem(db.Model):
    __tablename__ = "payslip_items"
    id = db.Column(db.Integer, primary_key=True)
    payslip_id = db.Column(db.Integer, db.ForeignKey("payslips.id", ondelete="CASCADE"), nullable=False)
    item_type = db.Column(db.Enum("ALLOWANCE", "DEDUCTION", name="payslip_item_type"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)


class OvertimeRequest(TenantMixin, db.Model):
    """Đơn đăng ký tăng ca — duyệt xong sẽ cộng tiền OT vào bảng lương tháng."""
    __tablename__ = "overtime_requests"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Numeric(4, 1), nullable=False)
    # Loại ngày tăng ca quyết định hệ số theo luật LĐ: thường 150%, cuối tuần 200%, lễ 300%
    ot_type = db.Column(db.Enum("WEEKDAY", "WEEKEND", "HOLIDAY", name="overtime_type"),
                        nullable=False, default="WEEKDAY")
    reason = db.Column(db.Text)
    status = db.Column(db.Enum("PENDING", "APPROVED", "REJECTED", name="overtime_status"),
                       default="PENDING")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    employee = db.relationship("Employee")

    # Hệ số lương tăng ca theo loại ngày
    MULTIPLIERS = {"WEEKDAY": 1.5, "WEEKEND": 2.0, "HOLIDAY": 3.0}

    @property
    def multiplier(self):
        return self.MULTIPLIERS.get(self.ot_type, 1.5)
