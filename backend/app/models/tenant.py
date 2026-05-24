"""
Model Tenant — đại diện cho một công ty/tổ chức sử dụng hệ thống.
Mỗi tenant là một không gian dữ liệu riêng biệt (multi-tenant).
"""

from app.extensions import db
from app.models.base import TimestampMixin


class Tenant(TimestampMixin, db.Model):
    """Bảng tenants — lưu thông tin tổ chức."""

    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Tên hiển thị của tổ chức
    name = db.Column(db.String(200), nullable=False)

    # Slug duy nhất — dùng trong URL hoặc subdomain (vd: "grapecorp")
    slug = db.Column(db.String(100), unique=True, nullable=False)

    # Thông tin pháp lý
    tax_id = db.Column(db.String(50))
    reg_number = db.Column(db.String(50))

    # Thông tin liên hệ
    phone = db.Column(db.String(30))
    email = db.Column(db.String(100))

    # Địa chỉ
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    address = db.Column(db.String(255))

    # URL logo công ty
    logo_url = db.Column(db.String(500))

    # Trạng thái hoạt động — False = tạm khóa tenant
    is_active = db.Column(db.Boolean, default=True)

    # Quan hệ 1-nhiều: một tenant có nhiều users
    users = db.relationship("User", backref="tenant", lazy="dynamic")

    def __repr__(self):
        return f"<Tenant {self.slug}>"
