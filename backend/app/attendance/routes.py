"""
Blueprint Attendance — chấm công (trung tâm hệ thống), ca làm việc,
địa điểm geofence và TỔNG CÔNG THÁNG.

    /api/attendance            — nhật ký chấm công (log)
    /api/attendance/check-in   — nhân viên tự chấm vào (GPS)
    /api/attendance/check-out  — nhân viên tự chấm ra (GPS)
    /api/attendance/summary    — tổng công tháng (tính động, không nhập tay)
    /api/work-shifts           — ca làm việc (nhiều ca, gán theo nhân viên)
    /api/work-locations        — địa điểm chấm công (geofence)
"""

from datetime import datetime, date, timedelta
import csv
import io

from flask import Blueprint, request, jsonify, g, Response
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import extract

from app.extensions import db
from app.models.attendance import Attendance
from app.models.work import WorkLocation, WorkShift
from app.models.employee import Employee
from app.models.user import User
from app.services.geo import nearest_location
from app.services import attendance_service as svc


def check_hr_admin():
    return get_jwt().get("role") in ["super_admin", "admin", "hr_manager"]


def _fmt_time(t):
    """Định dạng cột Time về chuỗi 'HH:MM' an toàn (xử lý time / timedelta / str)."""
    if t is None:
        return None
    if isinstance(t, str):
        return t[:5]
    if isinstance(t, timedelta):
        total = int(t.total_seconds())
        return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    return str(t)


def _parse_time(s):
    if not s:
        return None
    return datetime.strptime(s, "%H:%M").time()


def _current_employee():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.employee_id:
        return None
    return Employee.query.filter_by(id=user.employee_id, tenant_id=g.tenant_id).first()


def _serialize_attendance(r):
    return {
        "id": r.id,
        "employee_id": r.employee_id,
        "employee_name": r.employee.full_name(),
        "date": r.date.isoformat(),
        "check_in": _fmt_time(r.check_in),
        "check_out": _fmt_time(r.check_out),
        "work_hours": float(r.work_hours) if r.work_hours else 0,
        "status": r.status,
        "late_minutes": r.late_minutes or 0,
        "early_minutes": r.early_minutes or 0,
        "note": r.note,
        "source": r.source,
        "ip_verified": r.ip_verified,
    }


# ── 1. NHẬT KÝ CHẤM CÔNG ────────────────────────────────────────────────
attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


@attendance_bp.route("", methods=["GET"])
@jwt_required()
def get_attendance():
    month = request.args.get("month")
    year = request.args.get("year")
    emp_id = request.args.get("employee_id")

    query = Attendance.query.filter_by(tenant_id=g.tenant_id)

    # Nhân viên thường chỉ xem được của chính mình
    if not check_hr_admin():
        emp = _current_employee()
        if not emp:
            return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400
        query = query.filter_by(employee_id=emp.id)
    elif emp_id:
        query = query.filter_by(employee_id=emp_id)

    if month:
        query = query.filter(extract('month', Attendance.date) == int(month))
    if year:
        query = query.filter(extract('year', Attendance.date) == int(year))

    records = query.order_by(Attendance.date.desc()).all()
    return jsonify([_serialize_attendance(r) for r in records]), 200


@attendance_bp.route("", methods=["POST"])
@jwt_required()
def create_attendance():
    """HR thêm chấm công thủ công. Trạng thái tự suy ra từ giờ + ca nếu không chọn."""
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json(silent=True) or {}

    emp_id = data.get("employee_id")
    if not emp_id or not data.get("date"):
        return jsonify({"error": "Thiếu nhân viên hoặc ngày"}), 400

    emp = Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first()
    if not emp:
        return jsonify({"error": "Nhân viên không hợp lệ"}), 400

    try:
        att_date = datetime.strptime(str(data["date"]), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Ngày không hợp lệ"}), 400
    if att_date > date.today():
        return jsonify({"error": "Không thể chấm công cho ngày tương lai"}), 400

    check_in = _parse_time(data.get("check_in"))
    check_out = _parse_time(data.get("check_out"))
    if check_in and check_out and check_out <= check_in:
        return jsonify({"error": "Giờ ra phải sau giờ vào"}), 400

    shift = svc.resolve_shift(emp)
    derived_status, late_m, early_m = svc.derive_manual_status(check_in, check_out, shift)
    status = data.get("status") or derived_status
    work_hours = svc.calc_work_hours(check_in, check_out, shift.break_minutes if shift else 0)

    att = Attendance(
        tenant_id=g.tenant_id,
        employee_id=emp_id,
        date=att_date,
        check_in=check_in,
        check_out=check_out,
        work_hours=work_hours,
        status=status,
        late_minutes=late_m,
        early_minutes=early_m,
        note=data.get("note"),
        source="MANUAL",
    )
    db.session.add(att)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Nhân viên này đã có chấm công cho ngày đó"}), 400
    return jsonify({"message": "Thêm thành công", "id": att.id, "attendance": _serialize_attendance(att)}), 201


@attendance_bp.route("/<int:att_id>", methods=["PUT"])
@jwt_required()
def update_attendance(att_id):
    """HR/Admin sửa một dòng chấm công (vd: bổ sung giờ ra bị quên)."""
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    att = Attendance.query.filter_by(id=att_id, tenant_id=g.tenant_id).first()
    if not att:
        return jsonify({"error": "Không tìm thấy"}), 404

    data = request.get_json(silent=True) or {}
    if "check_in" in data:
        att.check_in = _parse_time(data["check_in"])
    if "check_out" in data:
        att.check_out = _parse_time(data["check_out"])
    if att.check_in and att.check_out and att.check_out <= att.check_in:
        return jsonify({"error": "Giờ ra phải sau giờ vào"}), 400
    if "note" in data:
        att.note = data["note"]

    shift = svc.resolve_shift(att.employee)
    att.work_hours = svc.calc_work_hours(att.check_in, att.check_out, shift.break_minutes if shift else 0)
    if data.get("status"):
        att.status = data["status"]
    else:
        att.status, att.late_minutes, att.early_minutes = svc.derive_manual_status(att.check_in, att.check_out, shift)
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công", "attendance": _serialize_attendance(att)}), 200


@attendance_bp.route("/<int:att_id>", methods=["DELETE"])
@jwt_required()
def delete_attendance(att_id):
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    att = Attendance.query.filter_by(id=att_id, tenant_id=g.tenant_id).first()
    if not att:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(att)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


# ── 2. NHÂN VIÊN TỰ CHẤM CÔNG (IP WHITELIST) ────────────────────────────

def _get_client_ip():
    """Lấy IP thực của client (ưu tiên X-Forwarded-For nếu sau reverse proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def _check_ip_whitelist(client_ip):
    """Kiểm tra IP client có nằm trong whitelist của bất kỳ địa điểm nào không.
    Trả về (True, location) nếu khớp, (False, None) nếu không."""
    locations = WorkLocation.query.filter_by(tenant_id=g.tenant_id, is_active=True).all()
    for loc in locations:
        if loc.allowed_ips:
            ip_list = [ip.strip() for ip in loc.allowed_ips.split(",") if ip.strip()]
            if client_ip in ip_list:
                return True, loc
    return False, None


@attendance_bp.route("/today", methods=["GET"])
@jwt_required()
def attendance_today():
    """Trạng thái chấm công hôm nay + ca áp dụng của nhân viên đang đăng nhập."""
    emp = _current_employee()
    if not emp:
        return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400
    att = Attendance.query.filter_by(employee_id=emp.id, date=date.today()).first()
    has_location = WorkLocation.query.filter_by(tenant_id=g.tenant_id, is_active=True).count() > 0
    shift = svc.resolve_shift(emp)
    client_ip = _get_client_ip()
    ip_ok, _ = _check_ip_whitelist(client_ip)
    return jsonify({
        "has_work_location": has_location,
        "shift": {
            "id": shift.id, "name": shift.name,
            "start_time": _fmt_time(shift.start_time), "end_time": _fmt_time(shift.end_time),
        } if shift else None,
        "attendance": _serialize_attendance(att) if att else None,
        "client_ip": client_ip,
        "ip_match": ip_ok,
    }), 200


@attendance_bp.route("/check-in", methods=["POST"])
@jwt_required()
def self_check_in():
    emp = _current_employee()
    if not emp:
        return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400

    # ── Xác thực bằng IP mạng văn phòng ──
    client_ip = _get_client_ip()
    ip_ok, loc = _check_ip_whitelist(client_ip)
    if not ip_ok:
        return jsonify({
            "error": f"IP của bạn ({client_ip}) không nằm trong mạng văn phòng. Hãy kết nối Wi-Fi/mạng LAN công ty để chấm công.",
            "client_ip": client_ip,
        }), 403

    today = date.today()
    att = Attendance.query.filter_by(employee_id=emp.id, date=today).first()
    if att and att.check_in:
        return jsonify({"error": "Bạn đã chấm công vào hôm nay rồi"}), 400
    if att and att.status == "ON_LEAVE":
        return jsonify({
            "error": "Bạn đang trong thời gian nghỉ phép đã được duyệt. Vui lòng hủy đơn nghỉ phép trước khi chấm công."
        }), 400

    now = datetime.now()
    shift = svc.resolve_shift(emp)  # ca gán riêng hoặc ca mặc định
    status, late_minutes = svc.evaluate_check_in(shift, now)

    if not att:
        att = Attendance(tenant_id=g.tenant_id, employee_id=emp.id, date=today, status=status)
        db.session.add(att)

    att.check_in = now.time()
    att.is_within_geofence = True
    att.ip_verified = True
    att.source = "SELF"
    att.status = status
    att.late_minutes = max(late_minutes, 0) if status == "LATE" else 0
    data = request.get_json(silent=True) or {}
    att.note = data.get("note") or att.note
    db.session.commit()

    return jsonify({
        "message": "Chấm công vào thành công" + (f" (đi muộn {att.late_minutes} phút)" if status == "LATE" else ""),
        "attendance": _serialize_attendance(att),
    }), 200


@attendance_bp.route("/check-out", methods=["POST"])
@jwt_required()
def self_check_out():
    emp = _current_employee()
    if not emp:
        return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400

    # ── Xác thực bằng IP mạng văn phòng ──
    client_ip = _get_client_ip()
    ip_ok, loc = _check_ip_whitelist(client_ip)
    if not ip_ok:
        return jsonify({
            "error": f"IP của bạn ({client_ip}) không nằm trong mạng văn phòng. Hãy kết nối Wi-Fi/mạng LAN công ty để chấm công.",
            "client_ip": client_ip,
        }), 403

    att = Attendance.query.filter_by(employee_id=emp.id, date=date.today()).first()
    if not att or not att.check_in:
        return jsonify({"error": "Bạn chưa chấm công vào hôm nay"}), 400
    if att.check_out:
        return jsonify({"error": "Bạn đã chấm công ra hôm nay rồi"}), 400

    shift = svc.resolve_shift(emp)
    svc.apply_check_out(att, shift, datetime.now())
    data = request.get_json(silent=True) or {}
    att.note = data.get("note") or att.note
    db.session.commit()

    msg = "Chấm công ra thành công"
    if att.status == "HALF_DAY":
        msg += " (tính nửa công)"
    elif att.status == "EARLY_LEAVE":
        msg += f" (về sớm {att.early_minutes} phút)"
    return jsonify({"message": msg, "attendance": _serialize_attendance(att)}), 200


# ── 3. TỔNG CÔNG THÁNG (tính động từ log — KHÔNG nhập tay) ──────────────

@attendance_bp.route("/summary", methods=["GET"])
@jwt_required()
def attendance_summary():
    """Bảng tổng công tháng. HR xem tất cả; nhân viên xem của chính mình."""
    today = date.today()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    emp_id = None
    if not check_hr_admin():
        emp = _current_employee()
        if not emp:
            return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400
        emp_id = emp.id
    elif request.args.get("employee_id"):
        emp_id = int(request.args.get("employee_id"))

    rows = svc.monthly_summary(g.tenant_id, year, month, employee_id=emp_id)
    return jsonify({"month": month, "year": year, "rows": rows}), 200


@attendance_bp.route("/summary/export", methods=["GET"])
@jwt_required()
def export_summary():
    """Xuất bảng tổng công tháng ra CSV (mở trực tiếp bằng Excel)."""
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    today = date.today()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    rows = svc.monthly_summary(g.tenant_id, year, month)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Mã NV", "Họ tên", "Phòng ban", "Công chuẩn", "Ngày đủ công", "Nửa công",
        "Thiếu chấm ra", "Đi muộn (lần)", "Đi muộn (phút)", "Về sớm (lần)",
        "Phép có lương", "Nghỉ không lương", "Vắng không phép", "OT (giờ)", "TỔNG CÔNG",
    ])
    for r in rows:
        writer.writerow([
            r["employee_code"], r["employee_name"], r["department"] or "",
            r["standard_days"], r["full_days"], r["half_days"], r["missing_checkout"],
            r["late_count"], r["late_minutes"], r["early_count"],
            r["paid_leave"], r["unpaid_leave"], r["absent_days"], r["ot_hours"],
            r["total_workdays"],
        ])
    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=tong_cong_{month}_{year}.csv"},
    )


@attendance_bp.route("/export", methods=["GET"])
@jwt_required()
def export_attendance():
    """Xuất nhật ký chấm công chi tiết ra CSV."""
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    month = request.args.get("month", date.today().month)
    year = request.args.get("year", date.today().year)

    records = Attendance.query.filter(
        Attendance.tenant_id == g.tenant_id,
        extract('month', Attendance.date) == int(month),
        extract('year', Attendance.date) == int(year),
    ).order_by(Attendance.date.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Mã NV", "Tên NV", "Ngày", "Check-in", "Check-out", "Giờ làm",
                     "Trạng thái", "Muộn (phút)", "Sớm (phút)", "Ghi chú"])
    for r in records:
        writer.writerow([
            r.employee.employee_id,
            r.employee.full_name(),
            r.date.strftime("%d/%m/%Y"),
            _fmt_time(r.check_in) or "",
            _fmt_time(r.check_out) or "",
            r.work_hours or 0,
            r.status,
            r.late_minutes or 0,
            r.early_minutes or 0,
            r.note or "",
        ])

    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendance_{month}_{year}.csv"},
    )


# ── 4. ĐỊA ĐIỂM LÀM VIỆC (GEOFENCE) ─────────────────────────────────────
work_location_bp = Blueprint("work_location", __name__, url_prefix="/api/work-locations")


@work_location_bp.route("", methods=["GET"])
@jwt_required()
def get_work_locations():
    locs = WorkLocation.query.filter_by(tenant_id=g.tenant_id).all()
    return jsonify([{
        "id": l.id,
        "name": l.name,
        "is_active": l.is_active,
        "allowed_ips": l.allowed_ips or "",
    } for l in locs]), 200


@work_location_bp.route("", methods=["POST"])
@jwt_required()
def create_work_location():
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Thiếu tên địa điểm"}), 400
    loc = WorkLocation(
        tenant_id=g.tenant_id,
        name=data["name"],
        is_active=data.get("is_active", True),
        allowed_ips=data.get("allowed_ips") or None,
    )
    db.session.add(loc)
    db.session.commit()
    return jsonify({"message": "Đã thêm địa điểm", "id": loc.id}), 201


@work_location_bp.route("/<int:loc_id>", methods=["PUT"])
@jwt_required()
def update_work_location(loc_id):
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    loc = WorkLocation.query.filter_by(id=loc_id, tenant_id=g.tenant_id).first()
    if not loc:
        return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}
    for f in ["name", "is_active", "allowed_ips"]:
        if f in data:
            setattr(loc, f, data[f])
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200


@work_location_bp.route("/<int:loc_id>", methods=["DELETE"])
@jwt_required()
def delete_work_location(loc_id):
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    loc = WorkLocation.query.filter_by(id=loc_id, tenant_id=g.tenant_id).first()
    if not loc:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(loc)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


# ── 5. CA LÀM VIỆC ──────────────────────────────────────────────────────
work_shift_bp = Blueprint("work_shift", __name__, url_prefix="/api/work-shifts")


@work_shift_bp.route("", methods=["GET"])
@jwt_required()
def get_work_shifts():
    shifts = WorkShift.query.filter_by(tenant_id=g.tenant_id).all()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "start_time": _fmt_time(s.start_time),
        "end_time": _fmt_time(s.end_time),
        "late_threshold_minutes": s.late_threshold_minutes,
        "break_minutes": s.break_minutes,
        "is_default": s.is_default,
        "assigned_count": Employee.query.filter_by(tenant_id=g.tenant_id, shift_id=s.id).count(),
    } for s in shifts]), 200


@work_shift_bp.route("", methods=["POST"])
@jwt_required()
def create_work_shift():
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("start_time") or not data.get("end_time"):
        return jsonify({"error": "Thiếu tên hoặc giờ ca"}), 400

    start_t, end_t = _parse_time(data["start_time"]), _parse_time(data["end_time"])
    if end_t <= start_t:
        return jsonify({"error": "Giờ ra ca phải sau giờ vào ca"}), 400

    is_default = data.get("is_default", False)
    if is_default:
        WorkShift.query.filter_by(tenant_id=g.tenant_id).update({"is_default": False})

    shift = WorkShift(
        tenant_id=g.tenant_id,
        name=data["name"],
        start_time=start_t,
        end_time=end_t,
        late_threshold_minutes=int(data.get("late_threshold_minutes", 15)),
        break_minutes=int(data.get("break_minutes", 60)),
        is_default=is_default,
    )
    db.session.add(shift)
    db.session.commit()
    return jsonify({"message": "Đã thêm ca làm", "id": shift.id}), 201


@work_shift_bp.route("/<int:shift_id>", methods=["PUT"])
@jwt_required()
def update_work_shift(shift_id):
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    shift = WorkShift.query.filter_by(id=shift_id, tenant_id=g.tenant_id).first()
    if not shift:
        return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}

    if data.get("is_default"):
        WorkShift.query.filter(
            WorkShift.tenant_id == g.tenant_id, WorkShift.id != shift.id
        ).update({"is_default": False})

    if "name" in data:
        shift.name = data["name"]
    if "start_time" in data:
        shift.start_time = _parse_time(data["start_time"])
    if "end_time" in data:
        shift.end_time = _parse_time(data["end_time"])
    from datetime import time as _time
    if (isinstance(shift.start_time, _time) and isinstance(shift.end_time, _time)
            and shift.end_time <= shift.start_time):
        return jsonify({"error": "Giờ ra ca phải sau giờ vào ca"}), 400
    if "late_threshold_minutes" in data:
        shift.late_threshold_minutes = int(data["late_threshold_minutes"])
    if "break_minutes" in data:
        shift.break_minutes = int(data["break_minutes"])
    if "is_default" in data:
        shift.is_default = data["is_default"]
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200


@work_shift_bp.route("/<int:shift_id>", methods=["DELETE"])
@jwt_required()
def delete_work_shift(shift_id):
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền"}), 403
    shift = WorkShift.query.filter_by(id=shift_id, tenant_id=g.tenant_id).first()
    if not shift:
        return jsonify({"error": "Không tìm thấy"}), 404
    assigned = Employee.query.filter_by(tenant_id=g.tenant_id, shift_id=shift.id).count()
    if assigned:
        return jsonify({"error": f"Ca này đang được gán cho {assigned} nhân viên. Hãy đổi ca cho họ trước."}), 400
    if shift.is_default:
        return jsonify({"error": "Không thể xóa ca mặc định. Hãy đặt ca khác làm mặc định trước."}), 400
    db.session.delete(shift)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200
