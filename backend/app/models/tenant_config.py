"""
Model TenantConfig — cấu hình riêng cho từng tenant (SMTP riêng, gói dịch vụ).
"""

from app.extensions import db


class TenantConfig(db.Model):
    __tablename__ = "tenant_configs"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False)

    # SMTP riêng (nếu không set → dùng cấu hình hệ thống)
    mail_server = db.Column(db.String(255))
    mail_port = db.Column(db.Integer)
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_username = db.Column(db.String(255))
    mail_password_encrypted = db.Column(db.Text)  # mã hóa Fernet, không lưu plaintext
    mail_default_sender = db.Column(db.String(255))

    # Gói dịch vụ
    max_employees = db.Column(db.Integer, default=50)
    plan = db.Column(db.Enum("FREE", "PRO", "ENTERPRISE", name="tenant_plan"), default="FREE")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
