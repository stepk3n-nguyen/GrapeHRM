"""
Model AuditLog — nhật ký hoạt động quan trọng để truy vết.
"""

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)         # CREATE/UPDATE/DELETE/LOGIN/APPROVE/REJECT...
    resource_type = db.Column(db.String(50), nullable=False)  # EMPLOYEE/LEAVE_REQUEST/PAYROLL/USER...
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)               # JSON mô tả thay đổi
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User")
