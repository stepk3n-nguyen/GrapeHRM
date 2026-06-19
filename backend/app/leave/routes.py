"""
Blueprint Leave — Xử lý nghiệp vụ Thời gian & Nghỉ phép.
Bao gồm các chức năng: Loại nghỉ phép, Chính sách, Đơn nghỉ phép, Số dư, Chấm công.
"""

from datetime import datetime, date, timedelta
import csv
import io
from flask import Blueprint, request, jsonify, g, Response, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import extract

from app.extensions import db
from app.models.leave import (
    LeaveType, LeavePolicy, LeavePolicyDetail, EmployeeLeavePolicy,
    LeaveRequest, LeaveApprovalLog, Attendance
)
from app.models.work import WorkLocation, WorkShift
from app.models.employee import Employee
from app.models.user import User
from app.services.geo import haversine_meters, nearest_location
from app.services.email_service import (
    send_leave_request_submitted_email,
    send_leave_final_approved_email,
    send_leave_rejected_email,
    send_leave_cancelled_email
)

def check_hr_admin():
    """Kiểm tra xem user hiện tại có role là admin hoặc hr_manager không."""
    claims = get_jwt()
    return claims.get("role") in ["super_admin", "admin", "hr_manager"]


def _fmt_time(t):
    """Định dạng cột Time về chuỗi 'HH:MM' an toàn (xử lý time / timedelta / str)."""
    if t is None:
        return None
    if isinstance(t, str):
        return t[:5]
    if isinstance(t, timedelta):
        # PyMySQL có thể trả TIME về dạng timedelta
        total = int(t.total_seconds())
        return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    return str(t)


def _current_employee():
    """Lấy hồ sơ Employee gắn với user đang đăng nhập (cùng tenant)."""
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.employee_id:
        return None
    return Employee.query.filter_by(id=user.employee_id, tenant_id=g.tenant_id).first()


def _count_working_days(start, end, half_day=False):
    """Đếm số ngày làm việc từ start..end (loại T7/CN VÀ ngày lễ có lương).
    Trả về số ngày (float). half_day=True và cùng 1 ngày → 0.5."""
    if end < start:
        return 0.0
    from app.services.calendar_service import working_days_between
    days = working_days_between(g.tenant_id, start, end)
    if half_day and start == end:
        return 0.5
    return float(days)


def _sync_leave_attendance(req, create):
    """Đồng bộ chấm công ON_LEAVE theo đơn nghỉ.

    create=True  → sinh bản ghi ON_LEAVE cho từng ngày làm việc trong đơn
                   (bỏ T7/CN và ngày lễ; không đụng vào ngày đã có chấm công).
    create=False → xóa các bản ghi ON_LEAVE trong khoảng ngày của đơn
                   (khi đơn bị từ chối/hủy sau khi đã duyệt).
    """
    from app.services.calendar_service import holiday_dates, is_working_day

    hol = set()
    for y in range(req.start_date.year, req.end_date.year + 1):
        hol |= holiday_dates(g.tenant_id, y)

    cur = req.start_date
    while cur <= req.end_date:
        existing = Attendance.query.filter_by(
            tenant_id=g.tenant_id, employee_id=req.employee_id, date=cur
        ).first()
        if create:
            if is_working_day(cur, hol) and existing is None:
                db.session.add(Attendance(
                    tenant_id=g.tenant_id, employee_id=req.employee_id, date=cur,
                    status="ON_LEAVE", source="MANUAL",
                    note=f"Nghỉ phép: {req.leave_type.name if req.leave_type else ''}".strip(),
                ))
        else:
            if existing is not None and existing.status == "ON_LEAVE":
                db.session.delete(existing)
        cur += timedelta(days=1)


# ── 1. BLUEPRINT: LOẠI NGHỈ PHÉP (LEAVE TYPES) ──────────────────────────
leave_type_bp = Blueprint("leave_type", __name__, url_prefix="/api/leave-types")

@leave_type_bp.route("", methods=["GET"])
@jwt_required()
def get_leave_types():
    tenant_id = g.tenant_id
    types = LeaveType.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([{
        "id": t.id,
        "name": t.name,
        "code": t.code,
        "is_paid": t.is_paid,
        "max_days": t.max_days,
        "description": t.description
    } for t in types]), 200

@leave_type_bp.route("", methods=["POST"])
@jwt_required()
def create_leave_type():
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền thực hiện"}), 403
    
    data = request.get_json(silent=True)
    if not data or not data.get("name") or not data.get("code"):
        return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400
        
    code = data["code"].upper()
    existing = LeaveType.query.filter_by(tenant_id=g.tenant_id, code=code).first()
    if existing:
        return jsonify({"error": "Mã loại nghỉ phép đã tồn tại"}), 400
        
    new_type = LeaveType(
        tenant_id=g.tenant_id,
        name=data["name"],
        code=code,
        is_paid=data.get("is_paid", True),
        max_days=data.get("max_days", 0),
        description=data.get("description")
    )
    db.session.add(new_type)
    db.session.commit()
    return jsonify({"message": "Tạo thành công", "id": new_type.id}), 201

@leave_type_bp.route("/<int:type_id>", methods=["PUT"])
@jwt_required()
def update_leave_type(type_id):
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền thực hiện"}), 403
        
    t = LeaveType.query.filter_by(id=type_id, tenant_id=g.tenant_id).first()
    if not t: return jsonify({"error": "Không tìm thấy"}), 404
    
    data = request.get_json(silent=True)
    if "name" in data: t.name = data["name"]
    if "is_paid" in data: t.is_paid = data["is_paid"]
    if "max_days" in data: t.max_days = data["max_days"]
    if "description" in data: t.description = data["description"]
    
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200

@leave_type_bp.route("/<int:type_id>", methods=["DELETE"])
@jwt_required()
def delete_leave_type(type_id):
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền thực hiện"}), 403
        
    t = LeaveType.query.filter_by(id=type_id, tenant_id=g.tenant_id).first()
    if not t: return jsonify({"error": "Không tìm thấy"}), 404
    
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "Xóa thành công"}), 200

# ── 2. BLUEPRINT: CHÍNH SÁCH (LEAVE POLICIES) ───────────────────────────
leave_policy_bp = Blueprint("leave_policy", __name__, url_prefix="/api/leave-policies")

@leave_policy_bp.route("", methods=["GET"])
@jwt_required()
def get_policies():
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    policies = LeavePolicy.query.filter_by(tenant_id=g.tenant_id).all()
    res = []
    for p in policies:
        details = [{"type_id": d.leave_type_id, "type_name": d.leave_type.name, "entitlement": d.entitlement} for d in p.details]
        res.append({
            "id": p.id,
            "name": p.name,
            "year_start_month": p.year_start_month,
            "is_default": p.is_default,
            "details": details
        })
    return jsonify(res), 200

@leave_policy_bp.route("", methods=["POST"])
@jwt_required()
def create_policy():
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json(silent=True)
    if not data or not data.get("name"): return jsonify({"error": "Thiếu dữ liệu"}), 400
    
    p = LeavePolicy(
        tenant_id=g.tenant_id,
        name=data["name"],
        year_start_month=data.get("year_start_month", 1),
        is_default=data.get("is_default", False)
    )
    db.session.add(p)
    db.session.flush()
    
    details = data.get("details", [])
    for d in details:
        pd = LeavePolicyDetail(policy_id=p.id, leave_type_id=d["type_id"], entitlement=d["entitlement"])
        db.session.add(pd)
        
    db.session.commit()
    return jsonify({"message": "Tạo chính sách thành công"}), 201

@leave_policy_bp.route("/<int:p_id>", methods=["PUT"])
@jwt_required()
def update_policy(p_id):
    """Cập nhật chính sách nghỉ phép — chỉ admin mới có quyền."""
    claims = get_jwt()
    if claims.get("role") not in ["super_admin", "admin"]:
        return jsonify({"error": "Chỉ admin mới có quyền sửa chính sách phép"}), 403

    p = LeavePolicy.query.filter_by(id=p_id, tenant_id=g.tenant_id).first()
    if not p:
        return jsonify({"error": "Không tìm thấy chính sách"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Thiếu dữ liệu"}), 400

    if "name" in data:
        p.name = data["name"]
    if "is_default" in data:
        p.is_default = data["is_default"]
        # Nếu đặt làm mặc định, bỏ cờ mặc định ở các chính sách khác
        if p.is_default:
            LeavePolicy.query.filter(
                LeavePolicy.tenant_id == g.tenant_id,
                LeavePolicy.id != p.id
            ).update({"is_default": False})

    # Cập nhật danh sách chi tiết (entitlement)
    if "details" in data:
        # Xóa details cũ
        LeavePolicyDetail.query.filter_by(policy_id=p.id).delete()
        # Thêm details mới
        for d in data["details"]:
            pd = LeavePolicyDetail(
                policy_id=p.id,
                leave_type_id=d["type_id"],
                entitlement=d["entitlement"]
            )
            db.session.add(pd)

    db.session.commit()
    return jsonify({"message": "Cập nhật chính sách thành công"}), 200

@leave_policy_bp.route("/<int:p_id>", methods=["DELETE"])
@jwt_required()
def delete_policy(p_id):
    """Xóa chính sách nghỉ phép — chỉ admin mới có quyền."""
    claims = get_jwt()
    if claims.get("role") not in ["super_admin", "admin"]:
        return jsonify({"error": "Chỉ admin mới có quyền xóa chính sách phép"}), 403

    p = LeavePolicy.query.filter_by(id=p_id, tenant_id=g.tenant_id).first()
    if not p:
        return jsonify({"error": "Không tìm thấy chính sách"}), 404
        
    if p.is_default:
        return jsonify({"error": "Không thể xóa chính sách mặc định. Hãy đặt chính sách khác làm mặc định trước."}), 400

    # Ensure related assignments are cleared if DB cascade isn't fully relied on
    EmployeeLeavePolicy.query.filter_by(policy_id=p.id).delete()

    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Xóa chính sách thành công"}), 200

@leave_policy_bp.route("/<int:p_id>/assign", methods=["POST"])
@jwt_required()
def assign_policy(p_id):
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json()
    emp_ids = data.get("employee_ids", [])
    year = data.get("effective_year", date.today().year)
    
    for eid in emp_ids:
        # Xóa gán cũ cùng năm
        EmployeeLeavePolicy.query.filter_by(employee_id=eid, effective_year=year).delete()
        # Thêm gán mới
        assign = EmployeeLeavePolicy(tenant_id=g.tenant_id, employee_id=eid, policy_id=p_id, effective_year=year)
        db.session.add(assign)
        
    db.session.commit()
    return jsonify({"message": f"Đã gán cho {len(emp_ids)} nhân viên"}), 200


# ── 3. BLUEPRINT: ĐƠN NGHỈ PHÉP (LEAVE REQUESTS) ────────────────────────
leave_request_bp = Blueprint("leave_request", __name__, url_prefix="/api/leave-requests")

@leave_request_bp.route("", methods=["POST"])
@jwt_required()
def create_request():
    data = request.get_json(silent=True) or {}
    claims = get_jwt()
    role = claims.get("role")

    # 1) Xác định nhân viên: employee chỉ được nộp cho CHÍNH MÌNH (vá rò rỉ quyền)
    if role == "employee":
        emp = _current_employee()
        if not emp:
            return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400
        emp_id = emp.id
    else:
        emp_id = data.get("employee_id")
        emp = Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first()
        if not emp:
            return jsonify({"error": "Nhân viên không hợp lệ"}), 400

    # 2) Loại nghỉ phép hợp lệ trong tenant
    leave_type = LeaveType.query.filter_by(id=data.get("leave_type_id"), tenant_id=g.tenant_id).first()
    if not leave_type:
        return jsonify({"error": "Loại nghỉ phép không hợp lệ"}), 400

    # 3) Validate ngày
    try:
        start_d = datetime.strptime(str(data.get("start_date")), "%Y-%m-%d").date()
        end_d = datetime.strptime(str(data.get("end_date")), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Ngày không hợp lệ"}), 400
    if start_d > end_d:
        return jsonify({"error": "Ngày bắt đầu phải trước hoặc bằng ngày kết thúc"}), 400

    # 4) Server TỰ TÍNH số ngày nghỉ (loại T7/CN) — không tin total_days từ client
    half_day = bool(data.get("half_day"))
    total_days = _count_working_days(start_d, end_d, half_day)
    if total_days <= 0:
        return jsonify({"error": "Khoảng ngày đã chọn không có ngày làm việc nào"}), 400

    # 5) Chặn trùng/chồng ngày với đơn đang chờ hoặc đã duyệt
    overlap = LeaveRequest.query.filter(
        LeaveRequest.employee_id == emp_id,
        LeaveRequest.status.in_(["PENDING_HR", "APPROVED"]),
        LeaveRequest.start_date <= end_d,
        LeaveRequest.end_date >= start_d,
    ).first()
    if overlap:
        return jsonify({"error": "Khoảng ngày này trùng với một đơn nghỉ phép khác"}), 400

    # 6) Enforce số dư phép (chỉ với loại phép có hạn mức trong chính sách)
    year = start_d.year
    assign = EmployeeLeavePolicy.query.filter_by(employee_id=emp_id, effective_year=year).first()
    policy = assign.policy if assign else LeavePolicy.query.filter_by(tenant_id=g.tenant_id, is_default=True).first()
    entitlement = 0
    if policy:
        detail = next((d for d in policy.details if d.leave_type_id == leave_type.id), None)
        entitlement = detail.entitlement if detail else 0
    if entitlement and entitlement > 0:
        existing = LeaveRequest.query.filter(
            LeaveRequest.employee_id == emp_id,
            LeaveRequest.leave_type_id == leave_type.id,
            extract('year', LeaveRequest.start_date) == year,
            LeaveRequest.status.in_(["APPROVED", "PENDING_HR"]),
        ).all()
        consumed = sum(float(r.total_days) for r in existing)
        remaining = entitlement - consumed
        if total_days > remaining:
            return jsonify({"error": f"Vượt quỹ phép: chỉ còn {remaining:g} ngày, bạn đang xin {total_days:g} ngày"}), 400

    initial_status = "APPROVED" if role == "hr_manager" else "PENDING_HR"

    req = LeaveRequest(
        tenant_id=g.tenant_id,
        employee_id=emp_id,
        leave_type_id=leave_type.id,
        start_date=start_d,
        end_date=end_d,
        total_days=total_days,
        reason=data.get("reason"),
        status=initial_status
    )
    db.session.add(req)
    
    # Nếu HR tự xin nghỉ, thêm log phê duyệt tự động
    if initial_status == "APPROVED":
        db.session.flush() # Lấy id của req trước
        user_id = get_jwt_identity()
        log = LeaveApprovalLog(request_id=req.id, approver_id=user_id, action="APPROVED", comment="Hệ thống tự động duyệt cho HR")
        db.session.add(log)
        
    db.session.commit()
    
    # Chỉ gửi email cho HR khác duyệt nếu đơn là PENDING_HR
    if initial_status == "PENDING_HR":
        hrs = User.query.filter_by(tenant_id=g.tenant_id, role="hr_manager", is_active=True).all()
        leave_type = LeaveType.query.get(req.leave_type_id)
        for hr in hrs:
            if hr.email:
                app = current_app._get_current_object()
                send_leave_request_submitted_email(
                    app,
                    hr_email=hr.email,
                    employee_name=emp.full_name(),
                    leave_type_name=leave_type.name,
                    start_date=req.start_date,
                    end_date=req.end_date
                )
            
    return jsonify({"message": "Nộp đơn thành công", "id": req.id}), 201

@leave_request_bp.route("", methods=["GET"])
@jwt_required()
def get_requests():
    tenant_id = g.tenant_id
    claims = get_jwt()
    role = claims.get("role")
    
    query = LeaveRequest.query.filter_by(tenant_id=tenant_id)

    # Filter theo status/tháng/năm từ params
    status = request.args.get("status")
    if status: query = query.filter_by(status=status)

    year = request.args.get("year")
    if year: query = query.filter(extract('year', LeaveRequest.start_date) == int(year))

    # Phân quyền xem đơn
    if role == "employee":
        # Nhân viên CHỈ xem đơn của chính mình — lấy từ token, không tin param
        emp = _current_employee()
        if not emp:
            return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400
        query = query.filter_by(employee_id=emp.id)
    else:
        # HR/Admin có thể lọc theo employee_id nếu truyền lên
        emp_id = request.args.get("employee_id")
        if emp_id:
            query = query.filter_by(employee_id=emp_id)

    reqs = query.order_by(LeaveRequest.created_at.desc()).all()
    res = []
    for r in reqs:
        res.append({
            "id": r.id,
            "employee_name": r.employee.full_name(),
            "leave_type": r.leave_type.name,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "total_days": float(r.total_days),
            "status": r.status,
            "created_at": r.created_at.isoformat()
        })
    return jsonify(res), 200

@leave_request_bp.route("/<int:req_id>/approve", methods=["PUT"])
@jwt_required()
def approve_request(req_id):
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    req = LeaveRequest.query.filter_by(id=req_id, tenant_id=g.tenant_id).first()
    if not req: return jsonify({"error": "Không tìm thấy"}), 404
    
    claims = get_jwt()
    role = claims.get("role")
    user_id = get_jwt_identity()
    
    data = request.get_json(silent=True) or {}
    comment = data.get("comment", "")
    
    if req.status == "PENDING_HR" and role in ["hr_manager", "admin", "super_admin"]:
        req.status = "APPROVED"
        log = LeaveApprovalLog(request_id=req.id, approver_id=user_id, action="APPROVED", comment=comment)
        db.session.add(log)
        from app.services.audit_service import log_action
        log_action("APPROVE", "LEAVE_REQUEST", req.id)
        # Tự sinh chấm công ON_LEAVE cho các ngày nghỉ đã duyệt
        _sync_leave_attendance(req, create=True)
        db.session.commit()
        
        # Email NV
        if req.employee.work_email:
            app = current_app._get_current_object()
            send_leave_final_approved_email(app, req.employee.work_email, req.leave_type.name, req.start_date, req.end_date)
        return jsonify({"message": "Đã phê duyệt hoàn tất"}), 200
        
    return jsonify({"error": "Trạng thái không hợp lệ để duyệt"}), 400

@leave_request_bp.route("/<int:req_id>/reject", methods=["PUT"])
@jwt_required()
def reject_request(req_id):
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    req = LeaveRequest.query.filter_by(id=req_id, tenant_id=g.tenant_id).first()
    if not req: return jsonify({"error": "Không tìm thấy"}), 404
    
    data = request.get_json(silent=True) or {}
    reason = data.get("comment", "")
    
    was_approved = req.status == "APPROVED"
    req.status = "REJECTED"
    req.rejection_reason = reason
    log = LeaveApprovalLog(request_id=req.id, approver_id=get_jwt_identity(), action="REJECTED", comment=reason)
    db.session.add(log)
    # Nếu đơn từng được duyệt → gỡ các bản ghi ON_LEAVE đã sinh
    if was_approved:
        _sync_leave_attendance(req, create=False)
    db.session.commit()
    
    if req.employee.work_email:
        app = current_app._get_current_object()
        send_leave_rejected_email(app, req.employee.work_email, req.leave_type.name, reason)
        
    return jsonify({"message": "Đã từ chối đơn"}), 200


@leave_request_bp.route("/<int:req_id>/cancel", methods=["PUT"])
@jwt_required()
def cancel_request(req_id):
    req = LeaveRequest.query.filter_by(id=req_id, tenant_id=g.tenant_id).first()
    if not req: return jsonify({"error": "Không tìm thấy"}), 404
    
    if req.status != "PENDING_HR":
        return jsonify({"error": "Chỉ có thể hủy khi đang chờ duyệt"}), 400
        
    req.status = "CANCELLED"
    db.session.commit()
    
    # Gửi email thông báo hủy cho tất cả HR
    hrs = User.query.filter_by(tenant_id=g.tenant_id, role="hr_manager", is_active=True).all()
    for hr in hrs:
        if hr.email:
            app = current_app._get_current_object()
            send_leave_cancelled_email(
                app,
                hr_email=hr.email,
                employee_name=req.employee.full_name(),
                leave_type_name=req.leave_type.name,
                start_date=req.start_date,
                end_date=req.end_date
            )
            
    return jsonify({"message": "Đã hủy đơn"}), 200


# ── 4. BLUEPRINT: SỐ DƯ PHÉP (LEAVE BALANCE) ────────────────────────────
leave_balance_bp = Blueprint("leave_balance", __name__, url_prefix="/api/leave-balance")

@leave_balance_bp.route("/<int:emp_id>", methods=["GET"])
@jwt_required()
def get_balance(emp_id):
    year = int(request.args.get("year", date.today().year))
    
    # 1. Tìm policy đang áp dụng
    assign = EmployeeLeavePolicy.query.filter_by(employee_id=emp_id, effective_year=year).first()
    
    # Nếu chưa gán cho năm nay, tìm policy mặc định
    if not assign:
        policy = LeavePolicy.query.filter_by(tenant_id=g.tenant_id, is_default=True).first()
    else:
        policy = assign.policy
        
    if not policy:
        return jsonify({"error": "Chưa có chính sách phép nào áp dụng"}), 404
        
    # 2. Lấy đơn đã duyệt và đang chờ trong năm
    reqs = LeaveRequest.query.filter(
        LeaveRequest.employee_id == emp_id,
        extract('year', LeaveRequest.start_date) == year,
        LeaveRequest.status.in_(["APPROVED", "PENDING_HR"])
    ).all()
    
    used_map = {}
    pending_map = {}
    for r in reqs:
        tid = r.leave_type_id
        if r.status == "APPROVED":
            used_map[tid] = used_map.get(tid, 0) + float(r.total_days)
        else:
            pending_map[tid] = pending_map.get(tid, 0) + float(r.total_days)
            
    # 3. Tổng hợp
    res = []
    for d in policy.details:
        ent = d.entitlement
        used = used_map.get(d.leave_type_id, 0)
        pending = pending_map.get(d.leave_type_id, 0)
        res.append({
            "type_id": d.leave_type_id,
            "type_name": d.leave_type.name,
            "entitlement": ent,
            "used": used,
            "pending": pending,
            "remaining": ent - used - pending
        })
        
    return jsonify(res), 200


# ── 5. BLUEPRINT: CHẤM CÔNG (ATTENDANCE) ────────────────────────────────
attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

@attendance_bp.route("", methods=["GET"])
@jwt_required()
def get_attendance():
    month = request.args.get("month")
    year = request.args.get("year")
    emp_id = request.args.get("employee_id")
    
    query = Attendance.query.filter_by(tenant_id=g.tenant_id)
    if emp_id: query = query.filter_by(employee_id=emp_id)
    if month: query = query.filter(extract('month', Attendance.date) == int(month))
    if year: query = query.filter(extract('year', Attendance.date) == int(year))
    
    records = query.order_by(Attendance.date.desc()).all()
    return jsonify([_serialize_attendance(r) for r in records]), 200


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
        "note": r.note,
        "source": r.source,
        "is_within_geofence": r.is_within_geofence,
        "check_in_distance_m": r.check_in_distance_m,
    }

def _parse_time(s):
    """Chuyển chuỗi 'HH:MM' thành datetime.time, None nếu rỗng."""
    if not s:
        return None
    return datetime.strptime(s, "%H:%M").time()


def _calc_work_hours(check_in, check_out, break_minutes=0):
    """Tính giờ công = (ra − vào) − nghỉ giữa ca. check_in/out là datetime.time."""
    if not check_in or not check_out:
        return 0
    today = date.today()
    diff = (datetime.combine(today, check_out) - datetime.combine(today, check_in)).total_seconds() / 3600
    diff -= (break_minutes or 0) / 60
    return round(max(diff, 0), 1)


@attendance_bp.route("", methods=["POST"])
@jwt_required()
def create_attendance():
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json(silent=True) or {}

    emp_id = data.get("employee_id")
    if not emp_id or not data.get("date"):
        return jsonify({"error": "Thiếu nhân viên hoặc ngày"}), 400

    # Đảm bảo nhân viên thuộc đúng tenant (vá rò rỉ cách ly dữ liệu)
    emp = Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first()
    if not emp:
        return jsonify({"error": "Nhân viên không hợp lệ"}), 400

    check_in = _parse_time(data.get("check_in"))
    check_out = _parse_time(data.get("check_out"))
    work_hours = _calc_work_hours(check_in, check_out)

    att = Attendance(
        tenant_id=g.tenant_id,
        employee_id=emp_id,
        date=data["date"],
        check_in=check_in,
        check_out=check_out,
        work_hours=work_hours,
        status=data.get("status", "PRESENT"),
        note=data.get("note"),
        source="MANUAL",
    )
    db.session.add(att)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Nhân viên này đã có chấm công cho ngày đó"}), 400
    return jsonify({"message": "Thêm thành công", "id": att.id}), 201


@attendance_bp.route("/<int:att_id>", methods=["PUT"])
@jwt_required()
def update_attendance(att_id):
    """HR/Admin sửa một dòng chấm công."""
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    att = Attendance.query.filter_by(id=att_id, tenant_id=g.tenant_id).first()
    if not att: return jsonify({"error": "Không tìm thấy"}), 404

    data = request.get_json(silent=True) or {}
    if "check_in" in data: att.check_in = _parse_time(data["check_in"])
    if "check_out" in data: att.check_out = _parse_time(data["check_out"])
    if "status" in data: att.status = data["status"]
    if "note" in data: att.note = data["note"]
    att.work_hours = _calc_work_hours(att.check_in, att.check_out)
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200


@attendance_bp.route("/<int:att_id>", methods=["DELETE"])
@jwt_required()
def delete_attendance(att_id):
    """HR/Admin xóa một dòng chấm công."""
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    att = Attendance.query.filter_by(id=att_id, tenant_id=g.tenant_id).first()
    if not att: return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(att)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


# ── Nhân viên tự chấm công (geofence) ───────────────────────────────────

@attendance_bp.route("/today", methods=["GET"])
@jwt_required()
def attendance_today():
    """Trạng thái chấm công hôm nay của nhân viên đang đăng nhập."""
    emp = _current_employee()
    if not emp:
        return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400
    att = Attendance.query.filter_by(employee_id=emp.id, date=date.today()).first()
    has_location = WorkLocation.query.filter_by(tenant_id=g.tenant_id, is_active=True).count() > 0
    return jsonify({
        "has_work_location": has_location,
        "attendance": _serialize_attendance(att) if att else None,
    }), 200


def _resolve_geofence(lat, lng):
    """Kiểm tra toạ độ có nằm trong phạm vi địa điểm công ty không.
    Trả về (ok, location, distance_m, error_response)."""
    if lat is None or lng is None:
        return False, None, None, (jsonify({"error": "Thiếu toạ độ vị trí"}), 400)
    locations = WorkLocation.query.filter_by(tenant_id=g.tenant_id, is_active=True).all()
    if not locations:
        return False, None, None, (jsonify({"error": "Công ty chưa cấu hình địa điểm làm việc. Liên hệ quản trị viên."}), 400)
    loc, dist = nearest_location(locations, lat, lng)
    if dist > loc.radius_meters:
        return False, loc, dist, (jsonify({
            "error": f"Bạn đang ngoài phạm vi công ty (cách {int(dist)}m, cho phép {loc.radius_meters}m).",
            "distance_m": int(dist),
        }), 403)
    return True, loc, dist, None


@attendance_bp.route("/check-in", methods=["POST"])
@jwt_required()
def self_check_in():
    emp = _current_employee()
    if not emp:
        return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400

    data = request.get_json(silent=True) or {}
    lat, lng = data.get("latitude"), data.get("longitude")
    ok, loc, dist, err = _resolve_geofence(lat, lng)
    if not ok:
        return err

    today = date.today()
    att = Attendance.query.filter_by(employee_id=emp.id, date=today).first()
    if att and att.check_in:
        return jsonify({"error": "Bạn đã chấm công vào hôm nay rồi"}), 400

    now_t = datetime.now().time()

    # Suy ra trạng thái đi muộn theo ca mặc định
    shift = WorkShift.query.filter_by(tenant_id=g.tenant_id, is_default=True).first()
    status = "PRESENT"
    if shift:
        late_cutoff = (datetime.combine(today, shift.start_time)
                       + timedelta(minutes=shift.late_threshold_minutes or 0)).time()
        if now_t > late_cutoff:
            status = "LATE"

    if not att:
        att = Attendance(tenant_id=g.tenant_id, employee_id=emp.id, date=today, status=status)
        db.session.add(att)

    att.check_in = now_t
    att.check_in_lat = lat
    att.check_in_lng = lng
    att.check_in_distance_m = int(dist)
    att.is_within_geofence = True
    att.source = "SELF"
    att.status = status
    db.session.commit()

    return jsonify({
        "message": "Chấm công vào thành công" + (" (đi muộn)" if status == "LATE" else ""),
        "attendance": _serialize_attendance(att),
    }), 200


@attendance_bp.route("/check-out", methods=["POST"])
@jwt_required()
def self_check_out():
    emp = _current_employee()
    if not emp:
        return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400

    data = request.get_json(silent=True) or {}
    lat, lng = data.get("latitude"), data.get("longitude")
    ok, loc, dist, err = _resolve_geofence(lat, lng)
    if not ok:
        return err

    att = Attendance.query.filter_by(employee_id=emp.id, date=date.today()).first()
    if not att or not att.check_in:
        return jsonify({"error": "Bạn chưa chấm công vào hôm nay"}), 400
    if att.check_out:
        return jsonify({"error": "Bạn đã chấm công ra hôm nay rồi"}), 400

    shift = WorkShift.query.filter_by(tenant_id=g.tenant_id, is_default=True).first()
    break_minutes = shift.break_minutes if shift else 0

    att.check_out = datetime.now().time()
    att.check_out_lat = lat
    att.check_out_lng = lng
    att.work_hours = _calc_work_hours(att.check_in, att.check_out, break_minutes)
    db.session.commit()

    return jsonify({
        "message": "Chấm công ra thành công",
        "attendance": _serialize_attendance(att),
    }), 200

@attendance_bp.route("/export", methods=["GET"])
@jwt_required()
def export_attendance():
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    month = request.args.get("month", date.today().month)
    year = request.args.get("year", date.today().year)
    
    records = Attendance.query.filter(
        Attendance.tenant_id == g.tenant_id,
        extract('month', Attendance.date) == int(month),
        extract('year', Attendance.date) == int(year)
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Mã NV", "Tên NV", "Ngày", "Check-in", "Check-out", "Giờ làm", "Trạng thái", "Ghi chú"])
    for r in records:
        writer.writerow([
            r.employee.employee_id,
            r.employee.full_name(),
            r.date.strftime("%d/%m/%Y"),
            _fmt_time(r.check_in) or "",
            _fmt_time(r.check_out) or "",
            r.work_hours or 0,
            r.status,
            r.note or ""
        ])

    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendance_{month}_{year}.csv"}
    )


# ── 6. BLUEPRINT: ĐỊA ĐIỂM LÀM VIỆC (WORK LOCATIONS) ────────────────────
work_location_bp = Blueprint("work_location", __name__, url_prefix="/api/work-locations")

@work_location_bp.route("", methods=["GET"])
@jwt_required()
def get_work_locations():
    locs = WorkLocation.query.filter_by(tenant_id=g.tenant_id).all()
    return jsonify([{
        "id": l.id,
        "name": l.name,
        "latitude": float(l.latitude),
        "longitude": float(l.longitude),
        "radius_meters": l.radius_meters,
        "is_active": l.is_active,
    } for l in locs]), 200

@work_location_bp.route("", methods=["POST"])
@jwt_required()
def create_work_location():
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json(silent=True) or {}
    if not data.get("name") or data.get("latitude") is None or data.get("longitude") is None:
        return jsonify({"error": "Thiếu tên hoặc toạ độ"}), 400
    loc = WorkLocation(
        tenant_id=g.tenant_id,
        name=data["name"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        radius_meters=int(data.get("radius_meters", 200)),
        is_active=data.get("is_active", True),
    )
    db.session.add(loc)
    db.session.commit()
    return jsonify({"message": "Đã thêm địa điểm", "id": loc.id}), 201

@work_location_bp.route("/<int:loc_id>", methods=["PUT"])
@jwt_required()
def update_work_location(loc_id):
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    loc = WorkLocation.query.filter_by(id=loc_id, tenant_id=g.tenant_id).first()
    if not loc: return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}
    for f in ["name", "latitude", "longitude", "radius_meters", "is_active"]:
        if f in data:
            setattr(loc, f, data[f])
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200

@work_location_bp.route("/<int:loc_id>", methods=["DELETE"])
@jwt_required()
def delete_work_location(loc_id):
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    loc = WorkLocation.query.filter_by(id=loc_id, tenant_id=g.tenant_id).first()
    if not loc: return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(loc)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


# ── 7. BLUEPRINT: CA LÀM VIỆC (WORK SHIFTS) ─────────────────────────────
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
    } for s in shifts]), 200

@work_shift_bp.route("", methods=["POST"])
@jwt_required()
def create_work_shift():
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("start_time") or not data.get("end_time"):
        return jsonify({"error": "Thiếu tên hoặc giờ ca"}), 400

    is_default = data.get("is_default", False)
    if is_default:
        WorkShift.query.filter_by(tenant_id=g.tenant_id).update({"is_default": False})

    shift = WorkShift(
        tenant_id=g.tenant_id,
        name=data["name"],
        start_time=_parse_time(data["start_time"]),
        end_time=_parse_time(data["end_time"]),
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
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    shift = WorkShift.query.filter_by(id=shift_id, tenant_id=g.tenant_id).first()
    if not shift: return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}

    if data.get("is_default"):
        WorkShift.query.filter(
            WorkShift.tenant_id == g.tenant_id, WorkShift.id != shift.id
        ).update({"is_default": False})

    if "name" in data: shift.name = data["name"]
    if "start_time" in data: shift.start_time = _parse_time(data["start_time"])
    if "end_time" in data: shift.end_time = _parse_time(data["end_time"])
    if "late_threshold_minutes" in data: shift.late_threshold_minutes = int(data["late_threshold_minutes"])
    if "break_minutes" in data: shift.break_minutes = int(data["break_minutes"])
    if "is_default" in data: shift.is_default = data["is_default"]
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200

@work_shift_bp.route("/<int:shift_id>", methods=["DELETE"])
@jwt_required()
def delete_work_shift(shift_id):
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    shift = WorkShift.query.filter_by(id=shift_id, tenant_id=g.tenant_id).first()
    if not shift: return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(shift)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200
