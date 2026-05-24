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
