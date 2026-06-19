"""
Calendar service — đếm ngày làm việc có loại trừ T7/CN VÀ ngày lễ.
Dùng chung cho: tính lương (ngày công chuẩn) và nghỉ phép (số ngày trừ quỹ).
"""

import calendar
from datetime import date, timedelta

from sqlalchemy import extract

from app.models.holiday import Holiday


def holiday_dates(tenant_id, year, month=None, paid_only=True):
    """Trả về set các ngày lễ của tenant trong năm (hoặc 1 tháng).

    paid_only=True: chỉ lấy lễ có hưởng lương (để loại khỏi denominator lương).
    """
    q = Holiday.query.filter(
        Holiday.tenant_id == tenant_id,
        extract("year", Holiday.date) == year,
    )
    if month:
        q = q.filter(extract("month", Holiday.date) == month)
    if paid_only:
        q = q.filter(Holiday.is_paid.is_(True))
    return {h.date for h in q.all()}


def is_working_day(d, holidays):
    """Ngày làm việc = T2–T6 và không phải ngày lễ."""
    return d.weekday() < 5 and d not in holidays


def count_standard_working_days(tenant_id, year, month):
    """Số ngày công chuẩn trong tháng = số ngày T2–T6 trừ đi ngày lễ có lương.

    Ý nghĩa: NV đi làm đủ các ngày-công-chuẩn này là nhận đủ lương; ngày lễ
    được trả lương nhưng không nằm trong mẫu số nên không làm giảm tỷ lệ.
    """
    hol = holiday_dates(tenant_id, year, month)
    _, days = calendar.monthrange(year, month)
    return sum(1 for dd in range(1, days + 1)
               if is_working_day(date(year, month, dd), hol))


def working_days_between(tenant_id, start, end):
    """Số ngày làm việc trong [start, end] (loại T7/CN và ngày lễ có lương)."""
    if end < start:
        return 0
    hol = set()
    for y in range(start.year, end.year + 1):
        hol |= holiday_dates(tenant_id, y)
    n = 0
    cur = start
    while cur <= end:
        if is_working_day(cur, hol):
            n += 1
        cur += timedelta(days=1)
    return n
