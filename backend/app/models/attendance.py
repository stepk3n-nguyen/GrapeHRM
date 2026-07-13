"""
Model Attendance — bản ghi chấm công theo ngày (trung tâm của hệ thống).

Trạng thái:
    PRESENT     — đi làm đúng giờ
    LATE        — đi muộn (quá ngưỡng cho phép của ca)
    EARLY_LEAVE — về sớm (quá ngưỡng cho phép của ca)
    HALF_DAY    — nửa công (giờ làm < 50% giờ chuẩn của ca)
    ON_LEAVE    — nghỉ phép (tự sinh khi đơn nghỉ được duyệt)
    ABSENT      — vắng mặt không phép

Nguyên tắc: mọi số liệu tổng công tháng đều được TÍNH từ bảng này
(xem app/services/attendance_service.py), không nhập tay.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class Attendance(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    work_hours = db.Column(db.Numeric(4, 1))
    status = db.Column(
        db.Enum('PRESENT', 'ABSENT', 'LATE', 'EARLY_LEAVE', 'HALF_DAY', 'ON_LEAVE',
                name='attendance_status'),
        nullable=False,
    )
    note = db.Column(db.Text)

    # Số phút đi muộn / về sớm so với ca (0 nếu đúng giờ) — phục vụ tổng công
    late_minutes = db.Column(db.Integer, nullable=False, default=0)
    early_minutes = db.Column(db.Integer, nullable=False, default=0)

    # True nếu chấm công được xác thực bằng IP whitelist
    ip_verified = db.Column(db.Boolean, default=False)
    # Nguồn dữ liệu: nhân viên tự chấm (SELF) hay HR nhập tay (MANUAL)
    source = db.Column(db.Enum('SELF', 'MANUAL', name='attendance_source'), default='MANUAL')

    __table_args__ = (db.UniqueConstraint('employee_id', 'date'),)

    employee = db.relationship("Employee", backref=db.backref("attendances", cascade="all, delete-orphan"))
