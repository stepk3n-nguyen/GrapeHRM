"""
Script seed dữ liệu ban đầu — chạy trong Flask app context.
Tạo tenant mặc định và tài khoản admin nếu chưa tồn tại.

Cách dùng: Được gọi tự động trong create_app() khi app khởi chạy.
"""

from app.extensions import db
from app.models.tenant import Tenant
from app.models.user import User


def seed_initial_data():
    """
    Tạo dữ liệu mẫu cho lần chạy đầu tiên.
    Nếu dữ liệu đã tồn tại thì bỏ qua — an toàn khi chạy lại nhiều lần.
    """

    # ── Tạo tenant mặc định ──────────────────────────────────────────
    tenant = Tenant.query.filter_by(slug="grapecorp").first()

    if tenant is None:
        tenant = Tenant(
            name="GrapeCorp",
            slug="grapecorp",
            country="Vietnam",
            city="Ho Chi Minh",
            address="123 Grape Street, District 1",
            is_active=True,
        )
        db.session.add(tenant)
        db.session.flush()  # Lấy id ngay mà chưa commit — cần cho bước tiếp theo
        print("[SEED] Đã tạo tenant: GrapeCorp")

    # ── Tạo tài khoản admin mặc định ────────────────────────────────
    admin = User.query.filter_by(username="admin", tenant_id=tenant.id).first()

    if admin is None:
        admin = User(
            tenant_id=tenant.id,
            username="admin",
            email="admin@grapecorp.com",
            role="admin",
            is_active=True,
        )
        # Mã hóa mật khẩu bằng bcrypt — đúng cách, không cần hardcode hash
        admin.set_password("admin123")
        db.session.add(admin)
        print("[SEED] Đã tạo tài khoản admin (mật khẩu: admin123)")

    db.session.commit()

    # ── Seed Dữ liệu nghỉ phép cơ bản (Leave Types) ─────────────────
    from app.models.leave import LeaveType, LeavePolicy, LeavePolicyDetail
    
    default_types = [
        {"name": "Nghỉ phép năm", "code": "ANNUAL", "is_paid": True, "max_days": 12},
        {"name": "Nghỉ ốm", "code": "SICK", "is_paid": True, "max_days": 5},
        {"name": "Nghỉ thai sản", "code": "MATERNITY", "is_paid": True, "max_days": 0},
        {"name": "Nghỉ không lương", "code": "UNPAID", "is_paid": False, "max_days": 0},
        {"name": "Nghỉ kết hôn", "code": "WEDDING", "is_paid": True, "max_days": 3},
        {"name": "Nghỉ tang chế", "code": "BEREAVEMENT", "is_paid": True, "max_days": 3},
    ]

    type_objects = {}
    for t_data in default_types:
        t = LeaveType.query.filter_by(tenant_id=tenant.id, code=t_data["code"]).first()
        if not t:
            t = LeaveType(tenant_id=tenant.id, **t_data)
            db.session.add(t)
            db.session.flush()
        type_objects[t_data["code"]] = t

    # ── Seed Chính sách phép mặc định ──────────────────────────────
    default_policy = LeavePolicy.query.filter_by(tenant_id=tenant.id, is_default=True).first()
    if not default_policy:
        default_policy = LeavePolicy(
            tenant_id=tenant.id,
            name="Chính sách phép chuẩn",
            year_start_month=1,
            is_default=True
        )
        db.session.add(default_policy)
        db.session.flush()

        # Tạo details cho policy mặc định
        for code, t_obj in type_objects.items():
            entitlement = 12 if code == "ANNUAL" else (5 if code == "SICK" else (3 if code in ["WEDDING", "BEREAVEMENT"] else 0))
            detail = LeavePolicyDetail(policy_id=default_policy.id, leave_type_id=t_obj.id, entitlement=entitlement)
            db.session.add(detail)
            
        print("[SEED] Đã tạo Leave Types và Policy mặc định")

    db.session.commit()
