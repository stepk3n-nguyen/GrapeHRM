"""
Blueprint Reports — thống kê & báo cáo tổng hợp (Admin/HR).
Tất cả query đều cách ly theo g.tenant_id.
"""

from datetime import date
import csv
import io

from flask import request, jsonify, g, Response
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import extract

from app.extensions import db
from app.models.employee import Employee, Department
from app.models.leave import LeaveRequest, LeaveType, Attendance
from app.models.user import User
from . import reports_bp


def _is_hr_admin():
    return get_jwt().get("role") in ["super_admin", "admin", "hr_manager"]


def _guard():
    if not _is_hr_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
    return None


def _age(birthday, today):
    if not birthday:
        return None
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


# ── 1. DASHBOARD STATS ──────────────────────────────────────────────────
@reports_bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    block = _guard()
    if block:
        return block

    tid = g.tenant_id
    today = date.today()
    employees = Employee.query.filter_by(tenant_id=tid).all()

    total = len(employees)
    active = sum(1 for e in employees if e.state == "ACTIVE")
    terminated = sum(1 for e in employees if e.state == "TERMINATED")
    new_hires = sum(1 for e in employees
                    if e.joined_date and e.joined_date.year == today.year and e.joined_date.month == today.month)

    pending = LeaveRequest.query.filter_by(tenant_id=tid, status="PENDING_HR").count()

    # Tỷ lệ chấm công tháng hiện tại
    att = Attendance.query.filter(
        Attendance.tenant_id == tid,
        extract("month", Attendance.date) == today.month,
        extract("year", Attendance.date) == today.year,
    ).all()
    present_like = sum(1 for a in att if a.status in ("PRESENT", "LATE"))
    rate = round(present_like / len(att) * 100, 1) if att else 0

    # Theo phòng ban
    dept_map = {d.id: d.name for d in Department.query.filter_by(tenant_id=tid).all()}
    dept_count = {}
    for e in employees:
        if e.state != "ACTIVE":
            continue
        name = dept_map.get(e.department_id, "Chưa phân bổ")
        dept_count[name] = dept_count.get(name, 0) + 1

    return jsonify({
        "total_employees": total,
        "active_employees": active,
        "terminated_employees": terminated,
        "new_hires_this_month": new_hires,
        "pending_leave_requests": pending,
        "attendance_rate_this_month": rate,
        "departments_summary": [{"name": k, "count": v} for k, v in sorted(dept_count.items(), key=lambda x: -x[1])],
    }), 200


# ── 2. BÁO CÁO NHÂN SỰ ──────────────────────────────────────────────────
@reports_bp.route("/employees", methods=["GET"])
@jwt_required()
def report_employees():
    block = _guard()
    if block:
        return block

    tid = g.tenant_id
    today = date.today()
    year = int(request.args.get("year", today.year))
    employees = Employee.query.filter_by(tenant_id=tid).all()

    # Biến động theo tháng
    monthly = []
    for m in range(1, 13):
        new = sum(1 for e in employees if e.joined_date and e.joined_date.year == year and e.joined_date.month == m)
        term = sum(1 for e in employees if e.end_date and e.end_date.year == year and e.end_date.month == m)
        # active tới cuối tháng m: đã vào trước/đúng tháng và chưa nghỉ trước tháng đó
        end_of_month = date(year, m, 28)
        active = sum(1 for e in employees
                     if e.joined_date and e.joined_date <= end_of_month
                     and (not e.end_date or e.end_date >= end_of_month))
        monthly.append({"month": m, "active": active, "new": new, "terminated": term})

    dept_map = {d.id: d.name for d in Department.query.filter_by(tenant_id=tid).all()}
    by_dept = {}
    gender = {"male": 0, "female": 0, "other": 0}
    age_group = {"18-25": 0, "26-35": 0, "36-45": 0, "46+": 0}
    tenures = []
    for e in employees:
        if e.state != "ACTIVE":
            continue
        dn = dept_map.get(e.department_id, "Chưa phân bổ")
        by_dept[dn] = by_dept.get(dn, 0) + 1
        if e.gender == 1:
            gender["male"] += 1
        elif e.gender == 2:
            gender["female"] += 1
        else:
            gender["other"] += 1
        a = _age(e.birthday, today)
        if a is not None:
            if a <= 25:
                age_group["18-25"] += 1
            elif a <= 35:
                age_group["26-35"] += 1
            elif a <= 45:
                age_group["36-45"] += 1
            else:
                age_group["46+"] += 1
        if e.joined_date:
            tenures.append((today - e.joined_date).days / 30.0)

    avg_tenure = round(sum(tenures) / len(tenures), 1) if tenures else 0

    return jsonify({
        "monthly_headcount": monthly,
        "by_department": [{"name": k, "count": v} for k, v in sorted(by_dept.items(), key=lambda x: -x[1])],
        "by_gender": gender,
        "by_age_group": age_group,
        "avg_tenure_months": avg_tenure,
    }), 200


# ── 3. BÁO CÁO NGHỈ PHÉP ────────────────────────────────────────────────
@reports_bp.route("/leave", methods=["GET"])
@jwt_required()
def report_leave():
    block = _guard()
    if block:
        return block

    tid = g.tenant_id
    year = int(request.args.get("year", date.today().year))

    reqs = LeaveRequest.query.filter(
        LeaveRequest.tenant_id == tid,
        LeaveRequest.status == "APPROVED",
        extract("year", LeaveRequest.start_date) == year,
    ).all()

    by_type = {}
    by_month = {m: 0 for m in range(1, 13)}
    by_user = {}
    for r in reqs:
        tname = r.leave_type.name if r.leave_type else "Khác"
        d = by_type.setdefault(tname, {"total_days": 0, "count": 0})
        d["total_days"] += float(r.total_days)
        d["count"] += 1
        by_month[r.start_date.month] += float(r.total_days)
        uname = r.employee.full_name() if r.employee else "?"
        by_user[uname] = by_user.get(uname, 0) + float(r.total_days)

    top_users = sorted(({"name": k, "total_days": v} for k, v in by_user.items()),
                       key=lambda x: -x["total_days"])[:5]

    return jsonify({
        "by_type": [{"type": k, **v} for k, v in by_type.items()],
        "by_month": [{"month": m, "total_days": by_month[m]} for m in range(1, 13)],
        "top_users": top_users,
    }), 200


# ── 4. BÁO CÁO CHẤM CÔNG ────────────────────────────────────────────────
@reports_bp.route("/attendance", methods=["GET"])
@jwt_required()
def report_attendance():
    block = _guard()
    if block:
        return block

    tid = g.tenant_id
    today = date.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    records = Attendance.query.filter(
        Attendance.tenant_id == tid,
        extract("year", Attendance.date) == year,
        extract("month", Attendance.date) == month,
    ).all()

    summary = {"total_records": len(records), "present": 0, "absent": 0, "late": 0, "on_leave": 0}
    by_emp = {}
    daily = {}
    for r in records:
        if r.status == "PRESENT":
            summary["present"] += 1
        elif r.status == "ABSENT":
            summary["absent"] += 1
        elif r.status == "LATE":
            summary["late"] += 1
        elif r.status == "ON_LEAVE":
            summary["on_leave"] += 1

        name = r.employee.full_name() if r.employee else "?"
        e = by_emp.setdefault(name, {"present": 0, "absent": 0, "late": 0, "hours": []})
        if r.status in ("PRESENT", "LATE"):
            e["present"] += 1
            if r.status == "LATE":
                e["late"] += 1
        elif r.status == "ABSENT":
            e["absent"] += 1
        if r.work_hours:
            e["hours"].append(float(r.work_hours))

        ds = r.date.isoformat()
        dd = daily.setdefault(ds, {"date": ds, "present": 0, "absent": 0, "late": 0})
        if r.status in ("PRESENT", "LATE"):
            dd["present"] += 1
            if r.status == "LATE":
                dd["late"] += 1
        elif r.status == "ABSENT":
            dd["absent"] += 1

    by_employee = [{
        "name": k,
        "present": v["present"], "absent": v["absent"], "late": v["late"],
        "work_hours_avg": round(sum(v["hours"]) / len(v["hours"]), 1) if v["hours"] else 0,
    } for k, v in by_emp.items()]

    return jsonify({
        "summary": summary,
        "by_employee": by_employee,
        "daily_trend": [daily[k] for k in sorted(daily.keys())],
    }), 200


# ── 5. EXPORT CSV ───────────────────────────────────────────────────────
def _csv_response(rows, header, filename):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@reports_bp.route("/employees/export", methods=["GET"])
@jwt_required()
def export_employees():
    block = _guard()
    if block:
        return block
    tid = g.tenant_id
    dept_map = {d.id: d.name for d in Department.query.filter_by(tenant_id=tid).all()}
    employees = Employee.query.filter_by(tenant_id=tid).all()
    rows = [[
        e.employee_id, e.full_name(),
        {1: "Nam", 2: "Nữ"}.get(e.gender, "Khác"),
        dept_map.get(e.department_id, ""),
        e.joined_date.strftime("%d/%m/%Y") if e.joined_date else "",
        "Đang làm" if e.state == "ACTIVE" else "Đã nghỉ",
    ] for e in employees]
    return _csv_response(rows, ["Mã NV", "Họ tên", "Giới tính", "Phòng ban", "Ngày vào", "Trạng thái"], "employees.csv")
