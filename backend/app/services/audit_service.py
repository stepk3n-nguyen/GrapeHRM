"""
Helper ghi nhật ký hoạt động (Audit Log).
Gọi trong request context; KHÔNG commit ở đây — để route gọi commit chung.
"""

import json

from flask import g, request

from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(action, resource_type, resource_id=None, details=None,
               tenant_id=None, user_id=None):
    """Thêm 1 dòng audit log vào session hiện tại."""
    try:
        log = AuditLog(
            tenant_id=tenant_id if tenant_id is not None else getattr(g, "tenant_id", None),
            user_id=user_id if user_id is not None else _g_user_id(),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            ip_address=request.remote_addr if request else None,
        )
        db.session.add(log)
    except Exception:
        # Audit không được phép làm hỏng nghiệp vụ chính
        pass


def _g_user_id():
    uid = getattr(g, "user_id", None)
    try:
        return int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None
