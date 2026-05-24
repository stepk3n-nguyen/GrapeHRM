"""
Các mixin class dùng chung cho tất cả model trong hệ thống.
Mixin giúp tái sử dụng cột chung (tenant_id, created_at, updated_at)
mà không cần viết lại trong từng model.
"""

from datetime import datetime, timezone

from app.extensions import db


class TenantMixin:
    """
    Mixin cung cấp cột tenant_id — dùng cho mọi bảng cần cách ly dữ liệu
    giữa các công ty (multi-tenant isolation).
    """

    tenant_id = db.Column(
        db.Integer,
        db.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class TimestampMixin:
    """
    Mixin tự động thêm cột created_at và updated_at.
    updated_at tự cập nhật mỗi khi row bị thay đổi.
    """

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
