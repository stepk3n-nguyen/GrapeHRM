"""
Danh mục ngày lễ pháp định Việt Nam — dùng chung cho seed & API "Nạp lễ VN".

QUAN TRỌNG (multi-tenant): ngày lễ là dữ liệu RIÊNG của từng công ty (tenant).
Danh sách dưới đây chỉ là GỢI Ý theo lịch nhà nước để khởi tạo nhanh; mỗi công ty
có thể tự thêm/bớt/xóa hết cho khớp lịch nghỉ thực tế của mình (ít hơn, nhiều hơn,
hoặc không có ngày nào). Vì vậy mọi nơi cần seed đều đi qua hàm ở file này.
"""

from datetime import date

from sqlalchemy import extract

from app.extensions import db
from app.models.holiday import Holiday


# Lễ DƯƠNG LỊCH cố định — áp dụng cho mọi năm (is_recurring=True).
_FIXED = [
    (1, 1, "Tết Dương lịch"),
    (4, 30, "Ngày Giải phóng miền Nam"),
    (5, 1, "Quốc tế Lao động"),
    (9, 2, "Quốc khánh"),
]

# Lễ ÂM LỊCH (Tết Nguyên đán, Giỗ tổ Hùng Vương) đổi ngày dương theo từng năm.
# Chỉ liệt kê các năm đã tra cứu chắc chắn; năm khác sẽ cần nhập tay.
_LUNAR = {
    2026: [
        (2, 16, "Tết Nguyên đán (30 Tết)"),
        (2, 17, "Tết Nguyên đán (Mùng 1)"),
        (2, 18, "Tết Nguyên đán (Mùng 2)"),
        (2, 19, "Tết Nguyên đán (Mùng 3)"),
        (2, 20, "Tết Nguyên đán (Mùng 4)"),
        (4, 26, "Giỗ tổ Hùng Vương (10/3 ÂL)"),
    ],
}


def vn_holidays_for_year(year):
    """Trả về (list[(date, name, is_recurring)], has_lunar).

    has_lunar=False nghĩa là năm đó chưa có dữ liệu Tết/Giỗ tổ → chỉ seed lễ dương lịch,
    công ty cần tự thêm Tết theo lịch âm.
    """
    items = [(date(year, m, d), name, True) for m, d, name in _FIXED]
    lunar = _LUNAR.get(year, [])
    for m, d, name in lunar:
        items.append((date(year, m, d), name, False))
    return items, bool(lunar)


def seed_vn_holidays_for_tenant(tenant_id, year):
    """Thêm lễ pháp định VN cho 1 tenant + năm. Bỏ qua ngày đã có (idempotent).
    KHÔNG commit — để nơi gọi commit chung. Trả về (số_ngày_thêm, has_lunar)."""
    existing = {h.date for h in Holiday.query.filter(
        Holiday.tenant_id == tenant_id,
        extract("year", Holiday.date) == year,
    ).all()}

    items, has_lunar = vn_holidays_for_year(year)
    added = 0
    for d, name, recurring in items:
        if d not in existing:
            db.session.add(Holiday(tenant_id=tenant_id, name=name, date=d,
                                   is_paid=True, is_recurring=recurring))
            added += 1
    return added, has_lunar
