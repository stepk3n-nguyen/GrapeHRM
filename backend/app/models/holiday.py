"""
Model Holiday — lịch ngày lễ / nghỉ của từng tenant.
Dùng để loại trừ khỏi: ngày công chuẩn (tính lương), số ngày trừ quỹ phép.
Theo BLLĐ Việt Nam: ngày lễ là nghỉ có hưởng nguyên lương.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class Holiday(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, nullable=False)

    # Ngày lễ có hưởng lương (mặc định True). Nếu False → coi như ngày nghỉ
    # không lương của công ty (vd nghỉ thêm), không trừ vào denominator lương.
    is_paid = db.Column(db.Boolean, default=True, nullable=False)

    # Lễ lặp lại hằng năm (ví dụ 1/1, 30/4) — chỉ để gợi ý copy sang năm sau.
    is_recurring = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint("tenant_id", "date", name="uq_tenant_holiday_date"),
    )

    def __repr__(self):
        return f"<Holiday {self.date} {self.name}>"
