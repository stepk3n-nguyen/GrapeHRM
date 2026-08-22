"""
Attendance service — TOÀN BỘ logic nghiệp vụ chấm công tập trung tại đây.

Dùng chung cho: API chấm công, tổng công tháng, dashboard và tính lương —
đảm bảo không có 2 nơi tính ra 2 con số khác nhau.

Quy tắc nghiệp vụ (SME Việt Nam):
- Ca làm việc của nhân viên = ca gán riêng (employees.shift_id),
  nếu chưa gán thì dùng ca mặc định của công ty.
- Đi muộn  : check-in  > giờ vào ca + late_threshold_minutes  → LATE.
- Về sớm   : check-out < giờ ra ca − late_threshold_minutes   → EARLY_LEAVE.
- Nửa công : tổng giờ làm < 50% giờ công chuẩn của ca         → HALF_DAY.
- Vắng mặt : ngày làm việc đã qua mà không có bản ghi nào và không nghỉ phép.
- Thiếu chấm ra: có check-in nhưng không check-out (ngày đã qua) → tính 0.5 công
  và được đánh dấu để HR sửa lại.
- Tổng công = ngày đủ công + 0.5 × (nửa công + thiếu chấm ra) + ngày phép có lương.
"""

from datetime import datetime, date, timedelta

from sqlalchemy import extract

from app.extensions import db
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest
from app.models.work import WorkShift
from app.models.employee import Employee
from app.models.compensation import OvertimeRequest
from app.services.calendar_service import holiday_dates, is_working_day

# Số công tính cho ngày có check-in nhưng quên check-out
MISSING_CHECKOUT_CREDIT = 0.5

# Các trạng thái được tính là "có đi làm đủ ngày"
FULL_DAY_STATUSES = ("PRESENT", "LATE", "EARLY_LEAVE")


# ────────────────────────────────────────────────────────────────────────
# Ca làm việc
# ────────────────────────────────────────────────────────────────────────

def resolve_shift(employee):
    """Ca áp dụng cho nhân viên: ca gán riêng → ca mặc định của tenant → None."""
    if employee.shift_id and employee.shift:
        return employee.shift
    return WorkShift.query.filter_by(tenant_id=employee.tenant_id, is_default=True).first()


def shift_standard_hours(shift):
    """Giờ công chuẩn của ca = (giờ ra − giờ vào) − nghỉ giữa ca."""
    if not shift:
        return 8.0
    ref = date(2000, 1, 1)
    total = (datetime.combine(ref, shift.end_time) - datetime.combine(ref, shift.start_time)).total_seconds() / 3600
    total -= (shift.break_minutes or 0) / 60
    return max(round(total, 2), 0.5)


def calc_work_hours(check_in, check_out, break_minutes=0):
    """Giờ công thực = (ra − vào) − nghỉ giữa ca. check_in/out là datetime.time."""
    if not check_in or not check_out:
        return 0
    ref = date(2000, 1, 1)
    diff = (datetime.combine(ref, check_out) - datetime.combine(ref, check_in)).total_seconds() / 3600
    diff -= (break_minutes or 0) / 60
    return round(max(diff, 0), 1)


# ────────────────────────────────────────────────────────────────────────
# Check-in / Check-out (nhận `now` tường minh để test được)
# ────────────────────────────────────────────────────────────────────────

def evaluate_check_in(shift, now=None):
    """Trạng thái + số phút muộn tại thời điểm check-in.

    Returns: (status, late_minutes)
    """
    now = now or datetime.now()
    if not shift:
        return "PRESENT", 0
    threshold = shift.late_threshold_minutes or 0
    start_dt = datetime.combine(now.date(), shift.start_time)
    late = int((now - start_dt).total_seconds() // 60)
    if late > threshold:
        return "LATE", late
    return "PRESENT", 0


def apply_check_out(att, shift, now=None):
    """Cập nhật bản ghi khi check-out: giờ công, về sớm, nửa công.

    Ưu tiên trạng thái: HALF_DAY > LATE > EARLY_LEAVE > PRESENT.
    (LATE giữ nguyên nếu đã muộn; về sớm chỉ đè khi trước đó PRESENT.)
    """
    now = now or datetime.now()
    att.check_out = now.time()
    break_minutes = shift.break_minutes if shift else 0
    att.work_hours = calc_work_hours(att.check_in, att.check_out, break_minutes)

    if not shift:
        return att

    threshold = shift.late_threshold_minutes or 0
    end_dt = datetime.combine(now.date(), shift.end_time)
    early = int((end_dt - now).total_seconds() // 60)
    att.early_minutes = max(early, 0) if early > threshold else 0

    standard = shift_standard_hours(shift)
    if float(att.work_hours or 0) < standard * 0.5:
        att.status = "HALF_DAY"
    elif att.early_minutes > 0 and att.status == "PRESENT":
        att.status = "EARLY_LEAVE"
    return att


def derive_manual_status(check_in, check_out, shift):
    """Suy ra trạng thái khi HR nhập tay giờ vào/ra mà không chọn trạng thái."""
    if not check_in:
        return "ABSENT", 0, 0
    threshold = (shift.late_threshold_minutes or 0) if shift else 0
    late_minutes = 0
    early_minutes = 0
    status = "PRESENT"
    if shift:
        ref = date(2000, 1, 1)
        late = int((datetime.combine(ref, check_in) - datetime.combine(ref, shift.start_time)).total_seconds() // 60)
        if late > threshold:
            status, late_minutes = "LATE", late
        if check_out:
            early = int((datetime.combine(ref, shift.end_time) - datetime.combine(ref, check_out)).total_seconds() // 60)
            if early > threshold:
                early_minutes = early
                if status == "PRESENT":
                    status = "EARLY_LEAVE"
            hours = calc_work_hours(check_in, check_out, shift.break_minutes or 0)
            if hours < shift_standard_hours(shift) * 0.5:
                status = "HALF_DAY"
    return status, max(late_minutes, 0), early_minutes


# ────────────────────────────────────────────────────────────────────────
# Nghỉ phép đã duyệt trong tháng (paid / unpaid) — nguồn: LeaveRequest
# ────────────────────────────────────────────────────────────────────────

def leave_days_in_month(tenant_id, emp_id, year, month, holidays):
    """(paid_days, unpaid_days) từ các đơn ĐÃ DUYỆT, phần giao với tháng.
    Loại T7/CN và ngày lễ. Đơn nửa ngày (total_days=0.5) giữ nguyên 0.5."""
    import calendar as _cal
    month_start = date(year, month, 1)
    month_end = date(year, month, _cal.monthrange(year, month)[1])
    reqs = LeaveRequest.query.filter(
        LeaveRequest.employee_id == emp_id,
        LeaveRequest.status == "APPROVED",
        LeaveRequest.start_date <= month_end,
        LeaveRequest.end_date >= month_start,
    ).all()
    paid = unpaid = 0.0
    for r in reqs:
        seg_start = max(r.start_date, month_start)
        seg_end = min(r.end_date, month_end)
        days = 0.0
        cur = seg_start
        while cur <= seg_end:
            if is_working_day(cur, holidays):
                days += 1
            cur += timedelta(days=1)
        # Đơn nửa ngày: tôn trọng total_days do server đã tính
        if float(r.total_days) < days:
            days = float(r.total_days)
        if r.leave_type and not r.leave_type.is_paid:
            unpaid += days
        else:
            paid += days
    return paid, unpaid


# ────────────────────────────────────────────────────────────────────────
# TỔNG CÔNG THÁNG — tính động 100% từ dữ liệu chấm công + phép + OT
# ────────────────────────────────────────────────────────────────────────

def monthly_summary(tenant_id, year, month, employee_id=None, today=None):
    """Bảng tổng công tháng cho từng nhân viên (không nhập tay).

    Returns: list[dict] — mỗi dict gồm:
        employee_id, employee_code, employee_name, department,
        standard_days, full_days, half_days, missing_checkout,
        late_count, late_minutes, early_count,
        paid_leave, unpaid_leave, absent_days, ot_hours, total_workdays
    """
    import calendar as _cal
    today = today or date.today()
    holidays = holiday_dates(tenant_id, year, month=None)  # cả năm để giao đơn phép
    month_holidays = {h for h in holidays if h.month == month and h.year == year}

    month_start = date(year, month, 1)
    month_end = date(year, month, _cal.monthrange(year, month)[1])
    standard_days = sum(
        1 for i in range((month_end - month_start).days + 1)
        if is_working_day(month_start + timedelta(days=i), month_holidays)
    )
    # Chỉ xét vắng mặt cho các ngày ĐÃ QUA (không kết tội tương lai)
    absent_cutoff = min(month_end, today - timedelta(days=1))

    emp_q = Employee.query.filter_by(tenant_id=tenant_id)
    if employee_id:
        emp_q = emp_q.filter_by(id=employee_id)
    employees = emp_q.all()

    att_q = Attendance.query.filter(
        Attendance.tenant_id == tenant_id,
        extract("year", Attendance.date) == year,
        extract("month", Attendance.date) == month,
    )
    if employee_id:
        att_q = att_q.filter(Attendance.employee_id == employee_id)
    att_by_emp = {}
    for a in att_q.all():
        att_by_emp.setdefault(a.employee_id, {})[a.date] = a

    ot_q = OvertimeRequest.query.filter(
        OvertimeRequest.tenant_id == tenant_id,
        OvertimeRequest.status == "APPROVED",
        extract("year", OvertimeRequest.date) == year,
        extract("month", OvertimeRequest.date) == month,
    )
    if employee_id:
        ot_q = ot_q.filter(OvertimeRequest.employee_id == employee_id)
    ot_by_emp = {}
    for o in ot_q.all():
        ot_by_emp[o.employee_id] = ot_by_emp.get(o.employee_id, 0.0) + float(o.hours)

    # Tập ngày nằm trong đơn phép ĐÃ DUYỆT (để không tính nhầm là vắng mặt)
    leave_reqs = LeaveRequest.query.filter(
        LeaveRequest.tenant_id == tenant_id,
        LeaveRequest.status == "APPROVED",
        LeaveRequest.start_date <= month_end,
        LeaveRequest.end_date >= month_start,
    )
    if employee_id:
        leave_reqs = leave_reqs.filter(LeaveRequest.employee_id == employee_id)
    leave_dates_by_emp = {}
    for r in leave_reqs.all():
        s = leave_dates_by_emp.setdefault(r.employee_id, set())
        cur = max(r.start_date, month_start)
        end = min(r.end_date, month_end)
        while cur <= end:
            s.add(cur)
            cur += timedelta(days=1)

    rows = []
    for emp in employees:
        # Nhân viên nghỉ việc trước tháng này → bỏ qua
        if emp.end_date and emp.end_date < month_start:
            continue
        # Nhân viên vào sau tháng này → bỏ qua
        if emp.joined_date and emp.joined_date > month_end:
            continue

        records = att_by_emp.get(emp.id, {})
        full = half = missing = late_cnt = early_cnt = 0
        late_min = 0
        for d, a in records.items():
            if a.status == "ON_LEAVE":
                continue  # phép tính từ LeaveRequest, tránh đếm 2 lần
            if a.status == "ABSENT":
                continue  # cộng vào absent bên dưới qua vòng quét ngày
            if a.check_in and not a.check_out and d < today:
                missing += 1
            elif a.status == "HALF_DAY":
                half += 1
            elif a.status in FULL_DAY_STATUSES:
                full += 1
            if a.status == "LATE":
                late_cnt += 1
                late_min += a.late_minutes or 0
            if a.status == "EARLY_LEAVE" or (a.early_minutes or 0) > 0:
                early_cnt += 1

        paid_leave, unpaid_leave = leave_days_in_month(tenant_id, emp.id, year, month, holidays)

        # Vắng mặt: ngày làm việc đã qua, trong thời gian còn làm việc,
        # không có bản ghi chấm công (hoặc bản ghi ABSENT) và không nằm trong đơn phép
        absent = 0
        scan_start = max(month_start, emp.joined_date or month_start)
        scan_end = absent_cutoff
        if emp.end_date:
            scan_end = min(scan_end, emp.end_date)
        emp_leave_dates = leave_dates_by_emp.get(emp.id, set())
        cur = scan_start
        while cur <= scan_end:
            if is_working_day(cur, month_holidays) and cur not in emp_leave_dates:
                rec = records.get(cur)
                if rec is None or rec.status == "ABSENT":
                    absent += 1
            cur += timedelta(days=1)

        ot_hours = round(ot_by_emp.get(emp.id, 0.0), 1)
        total = full + 0.5 * half + MISSING_CHECKOUT_CREDIT * missing + paid_leave

        rows.append({
            "employee_id": emp.id,
            "employee_code": emp.employee_id,
            "employee_name": emp.full_name(),
            "department": emp.department.name if emp.department else None,
            "state": emp.state,
            "standard_days": standard_days,
            "full_days": full,
            "half_days": half,
            "missing_checkout": missing,
            "late_count": late_cnt,
            "late_minutes": late_min,
            "early_count": early_cnt,
            "paid_leave": paid_leave,
            "unpaid_leave": unpaid_leave,
            "absent_days": absent,
            "ot_hours": ot_hours,
            "total_workdays": round(total, 1),
        })
    return rows


def summary_for_employee(tenant_id, emp_id, year, month, today=None):
    """Tổng công tháng của 1 nhân viên (dùng cho payroll)."""
    rows = monthly_summary(tenant_id, year, month, employee_id=emp_id, today=today)
    return rows[0] if rows else None


# ────────────────────────────────────────────────────────────────────────
# Thống kê HÔM NAY — cho dashboard
# ────────────────────────────────────────────────────────────────────────

def today_stats(tenant_id, today=None):
    """Số liệu chấm công hôm nay: đi làm / đi muộn / nghỉ phép / chưa chấm."""
    today = today or date.today()
    active_emps = Employee.query.filter_by(tenant_id=tenant_id, state="ACTIVE").all()
    active_ids = {e.id for e in active_emps}

    records = Attendance.query.filter(
        Attendance.tenant_id == tenant_id,
        Attendance.date == today,
    ).all()

    present = late = on_leave = absent_marked = 0
    checked_ids = set()
    for a in records:
        if a.employee_id not in active_ids:
            continue
        checked_ids.add(a.employee_id)
        if a.status == "LATE":
            late += 1
            present += 1
        elif a.status in ("PRESENT", "EARLY_LEAVE", "HALF_DAY"):
            present += 1
        elif a.status == "ON_LEAVE":
            on_leave += 1
        elif a.status == "ABSENT":
            absent_marked += 1

    holidays = holiday_dates(tenant_id, today.year, month=today.month)
    working_today = is_working_day(today, holidays)
    not_checked = len(active_ids) - len(checked_ids) if working_today else 0

    total_active = len(active_ids)
    
    # Dù là ngày nghỉ nhưng nếu có người đi làm (present > 0) thì vẫn tính tỷ lệ
    if total_active > 0:
        if working_today or present > 0:
            rate = round(present / total_active * 100, 1)
        else:
            rate = 0.0
    else:
        rate = 0.0

    return {
        "date": today.isoformat(),
        "is_working_day": working_today,
        "total_active_employees": total_active,
        "present": present,
        "late": late,
        "on_leave": on_leave,
        "absent": absent_marked + (not_checked if working_today else 0),
        "not_checked_in": max(not_checked, 0),
        "attendance_rate": rate,
    }
