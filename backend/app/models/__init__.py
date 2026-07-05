"""
Package models — import tập trung tất cả model.
Khi cần dùng model ở nơi khác, chỉ cần:
    from app.models import Tenant, User, Employee
"""

from app.models.tenant import Tenant
from app.models.user import User
from app.models.employee import Employee, EmployeeSequence, JobTitle, Department
from app.models.leave import (
    LeaveType, LeavePolicy, LeavePolicyDetail, EmployeeLeavePolicy,
    LeaveRequest, LeaveApprovalLog
)
from app.models.attendance import Attendance
from app.models.work import WorkLocation, WorkShift
from app.models.compensation import (
    SalaryStructure, SalaryAllowance, SalaryDeduction, EmployeeSalary,
    PayrollRun, Payslip, PayslipItem, OvertimeRequest
)
from app.models.audit_log import AuditLog
from app.models.tenant_config import TenantConfig
from app.models.email_log import EmailLog
from app.models.holiday import Holiday

# Danh sách tất cả model — hỗ trợ Flask-Migrate phát hiện bảng tự động
__all__ = [
    "Tenant", "User", "Employee", "EmployeeSequence", "JobTitle", "Department",
    "LeaveType", "LeavePolicy", "LeavePolicyDetail", "EmployeeLeavePolicy",
    "LeaveRequest", "LeaveApprovalLog", "Attendance",
    "WorkLocation", "WorkShift",
    "SalaryStructure", "SalaryAllowance", "SalaryDeduction", "EmployeeSalary",
    "PayrollRun", "Payslip", "PayslipItem", "OvertimeRequest",
    "AuditLog", "TenantConfig", "EmailLog", "Holiday",
]
