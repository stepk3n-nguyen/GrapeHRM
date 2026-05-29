"""
Package models — import tập trung tất cả model.
Khi cần dùng model ở nơi khác, chỉ cần:
    from app.models import Tenant, User, Employee
"""

from app.models.tenant import Tenant
from app.models.user import User
from app.models.employee import Employee, EmployeeSequence, JobTitle, Department

# Danh sách tất cả model — hỗ trợ Flask-Migrate phát hiện bảng tự động
__all__ = ["Tenant", "User", "Employee", "EmployeeSequence", "JobTitle", "Department"]
