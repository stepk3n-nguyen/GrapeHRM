"""
Model EmailLog — lưu trữ lịch sử gửi email.
"""

from app.extensions import db
from app.models.base import TimestampMixin

class EmailLog(TimestampMixin, db.Model):
    """Bảng email_logs — lưu lịch sử gửi email (thành công/thất bại)."""

    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Ràng buộc với tenant
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True) # Có thể null nếu gửi test từ admin
    
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 'SENT' or 'FAILED'
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f"<EmailLog {self.recipient} - {self.status}>"
