"""
Logic tạo tenant mới + seed dữ liệu mặc định cho tenant.
Dùng cho: đăng ký tổ chức mới (public) và Super Admin tạo tenant.
"""

import re
from datetime import time, date

from app.extensions import db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.leave import LeaveType, LeavePolicy, LeavePolicyDetail
from app.models.work import WorkShift
from app.models.compensation import SalaryAllowance, SalaryDeduction
from app.models.tenant_config import TenantConfig
from app.services.vn_holidays import seed_vn_holidays_for_tenant

SLUG_RE = re.compile(r"^[a-z0-9-]{3,50}$")


def seed_tenant_defaults(tenant_id):
    """Seed Leave Types, Policy mặc định, ca làm, phụ cấp/khấu trừ, TenantConfig."""
    default_types = [
        {"name": "Nghỉ phép năm", "code": "ANNUAL", "is_paid": True, "max_days": 12},
        {"name": "Nghỉ ốm", "code": "SICK", "is_paid": True, "max_days": 5},
        {"name": "Nghỉ thai sản", "code": "MATERNITY", "is_paid": True, "max_days": 0},
        {"name": "Nghỉ không lương", "code": "UNPAID", "is_paid": False, "max_days": 0},
        {"name": "Nghỉ kết hôn", "code": "WEDDING", "is_paid": True, "max_days": 3},
        {"name": "Nghỉ tang chế", "code": "BEREAVEMENT", "is_paid": True, "max_days": 3},
    ]
    type_objs = {}
    for t in default_types:
        obj = LeaveType.query.filter_by(tenant_id=tenant_id, code=t["code"]).first()
        if not obj:
            obj = LeaveType(tenant_id=tenant_id, **t)
            db.session.add(obj)
            db.session.flush()
        type_objs[t["code"]] = obj

    if not LeavePolicy.query.filter_by(tenant_id=tenant_id, is_default=True).first():
        policy = LeavePolicy(tenant_id=tenant_id, name="Chính sách phép chuẩn", year_start_month=1, is_default=True)
        db.session.add(policy)
        db.session.flush()
        for code, obj in type_objs.items():
            ent = 12 if code == "ANNUAL" else (5 if code == "SICK" else (3 if code in ("WEDDING", "BEREAVEMENT") else 0))
            db.session.add(LeavePolicyDetail(policy_id=policy.id, leave_type_id=obj.id, entitlement=ent))

    if not WorkShift.query.filter_by(tenant_id=tenant_id, is_default=True).first():
        db.session.add(WorkShift(tenant_id=tenant_id, name="Ca hành chính",
                                 start_time=time(8, 30), end_time=time(17, 30),
                                 late_threshold_minutes=15, break_minutes=60, is_default=True))

    if SalaryAllowance.query.filter_by(tenant_id=tenant_id).count() == 0:
        for name, amt in [("Phụ cấp ăn trưa", 730000), ("Phụ cấp xăng xe", 300000)]:
            db.session.add(SalaryAllowance(tenant_id=tenant_id, name=name, type="FIXED", default_amount=amt))
    if SalaryDeduction.query.filter_by(tenant_id=tenant_id).count() == 0:
        for name, pct in [("BHXH (8%)", 8), ("BHYT (1.5%)", 1.5), ("BHTN (1%)", 1)]:
            db.session.add(SalaryDeduction(tenant_id=tenant_id, name=name, type="PERCENT", default_amount=pct))

    if not TenantConfig.query.filter_by(tenant_id=tenant_id).first():
        db.session.add(TenantConfig(tenant_id=tenant_id, plan="FREE", max_employees=50))

    # Lịch ngày lễ nhà nước cho năm hiện tại làm ĐIỂM XUẤT PHÁT — công ty tự
    # thêm/bớt/xóa sau cho khớp lịch nghỉ thực tế (có thể ít hơn, nhiều hơn, hoặc bỏ hết).
    from app.models.holiday import Holiday
    if Holiday.query.filter_by(tenant_id=tenant_id).count() == 0:
        seed_vn_holidays_for_tenant(tenant_id, date.today().year)


def create_tenant_with_admin(organization_name, slug, admin_username, admin_email,
                             admin_password, country=None, city=None):
    """Tạo tenant + tài khoản admin + seed mặc định. Trả về (tenant, error)."""
    slug = (slug or "").strip().lower()
    if not SLUG_RE.match(slug):
        return None, "Mã tổ chức chỉ gồm a-z, 0-9, dấu gạch ngang, tối thiểu 3 ký tự"
    if Tenant.query.filter_by(slug=slug).first():
        return None, f"Mã tổ chức '{slug}' đã được sử dụng"
    if not organization_name or not admin_username or not admin_password:
        return None, "Thiếu thông tin bắt buộc"

    tenant = Tenant(name=organization_name, slug=slug, country=country, city=city, is_active=True)
    db.session.add(tenant)
    db.session.flush()

    admin = User(tenant_id=tenant.id, username=admin_username, email=admin_email or "", role="admin", is_active=True)
    admin.set_password(admin_password)
    db.session.add(admin)

    seed_tenant_defaults(tenant.id)
    db.session.commit()
    return tenant, None
