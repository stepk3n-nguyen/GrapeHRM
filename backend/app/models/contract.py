"""
Model Contract — hợp đồng lao động của nhân viên.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class Contract(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    contract_number = db.Column(db.String(50))

    # Loại HĐ: thử việc / xác định thời hạn / không xác định thời hạn / thời vụ
    contract_type = db.Column(
        db.Enum("PROBATION", "FIXED_TERM", "INDEFINITE", "SEASONAL", name="contract_type"),
        nullable=False, default="FIXED_TERM",
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)          # null = không xác định thời hạn
    basic_salary = db.Column(db.Numeric(12, 2), nullable=True)
    signed_date = db.Column(db.Date, nullable=True)

    status = db.Column(
        db.Enum("ACTIVE", "EXPIRED", "TERMINATED", name="contract_status"),
        default="ACTIVE",
    )
    note = db.Column(db.Text)

    employee = db.relationship("Employee")
