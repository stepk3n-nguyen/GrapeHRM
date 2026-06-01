from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin

class LeaveType(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "leave_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    is_paid = db.Column(db.Boolean, default=True)
    max_days = db.Column(db.Integer, default=0)
    description = db.Column(db.String(255))

class LeavePolicy(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "leave_policies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year_start_month = db.Column(db.SmallInteger, default=1)
    is_default = db.Column(db.Boolean, default=False)

class LeavePolicyDetail(db.Model):
    __tablename__ = "leave_policy_details"
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('leave_policies.id', ondelete='CASCADE'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id', ondelete='CASCADE'), nullable=False)
    entitlement = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('policy_id', 'leave_type_id'),)
    
    policy = db.relationship("LeavePolicy", backref=db.backref("details", cascade="all, delete-orphan"))
    leave_type = db.relationship("LeaveType")

class EmployeeLeavePolicy(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "employee_leave_policies"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('leave_policies.id', ondelete='CASCADE'), nullable=False)
    effective_year = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('employee_id', 'effective_year'),)

    employee = db.relationship("Employee", backref=db.backref("leave_policies", cascade="all, delete-orphan"))
    policy = db.relationship("LeavePolicy")

class LeaveRequest(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "leave_requests"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Numeric(4, 1), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum('PENDING_HR', 'APPROVED', 'REJECTED', 'CANCELLED', name='leave_status'), default='PENDING_HR')
    rejection_reason = db.Column(db.Text)
    
    employee = db.relationship("Employee", backref=db.backref("leave_requests", cascade="all, delete-orphan"))
    leave_type = db.relationship("LeaveType")

class LeaveApprovalLog(TimestampMixin, db.Model):
    __tablename__ = "leave_approval_logs"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('leave_requests.id', ondelete='CASCADE'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.Enum('APPROVED', 'REJECTED', name='approval_action'), nullable=False)
    comment = db.Column(db.Text)

    request = db.relationship("LeaveRequest", backref=db.backref("approval_logs", cascade="all, delete-orphan"))
    approver = db.relationship("User")

class Attendance(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    work_hours = db.Column(db.Numeric(4, 1))
    status = db.Column(db.Enum('PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'ON_LEAVE', name='attendance_status'), nullable=False)
    note = db.Column(db.Text)
    __table_args__ = (db.UniqueConstraint('employee_id', 'date'),)
    
    employee = db.relationship("Employee", backref=db.backref("attendances", cascade="all, delete-orphan"))
