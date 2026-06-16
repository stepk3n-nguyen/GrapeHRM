"""
Blueprint Leave — Xử lý nghiệp vụ Thời gian & Nghỉ phép.
Bao gồm các chức năng: Loại nghỉ phép, Chính sách, Đơn nghỉ phép, Số dư, Chấm công.
"""

from datetime import datetime, date
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
from app.models.employee import Employee
from app.models.user import User
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
    data = request.get_json()
    emp_id = data.get("employee_id")
    # Tạm thời, user cần truyền employee_id của mình lên
    emp = Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first()
    if not emp: return jsonify({"error": "Nhân viên không hợp lệ"}), 400
    
    claims = get_jwt()
    role = claims.get("role")
    initial_status = "APPROVED" if role == "hr_manager" else "PENDING_HR"

    req = LeaveRequest(
        tenant_id=g.tenant_id,
        employee_id=emp_id,
        leave_type_id=data["leave_type_id"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        total_days=data["total_days"],
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
    
    emp_id = request.args.get("employee_id")
    if emp_id: query = query.filter_by(employee_id=emp_id)
    
    year = request.args.get("year")
    if year: query = query.filter(extract('year', LeaveRequest.start_date) == int(year))
    
    # Phân quyền xem đơn
    if role == "employee":
        # (TODO: Lấy emp_id của user hiện tại, tạm thời lấy qua param)
        if not emp_id: return jsonify({"error": "Yêu cầu employee_id"}), 400
        query = query.filter_by(employee_id=emp_id)
    elif role == "hr_manager" or role == "admin":
        if not status:
            pass # See all
            
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
    
    req.status = "REJECTED"
    req.rejection_reason = reason
    log = LeaveApprovalLog(request_id=req.id, approver_id=get_jwt_identity(), action="REJECTED", comment=reason)
    db.session.add(log)
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
    res = []
    for r in records:
        res.append({
            "id": r.id,
            "employee_id": r.employee_id,
            "employee_name": r.employee.full_name(),
            "date": r.date.isoformat(),
            "check_in": r.check_in.isoformat() if r.check_in else None,
            "check_out": r.check_out.isoformat() if r.check_out else None,
            "work_hours": float(r.work_hours) if r.work_hours else 0,
            "status": r.status,
            "note": r.note
        })
    return jsonify(res), 200

@attendance_bp.route("", methods=["POST"])
@jwt_required()
def create_attendance():
    if not check_hr_admin(): return jsonify({"error": "Không có quyền"}), 403
    data = request.get_json()
    
    # Calc hours
    check_in = data.get("check_in")
    check_out = data.get("check_out")
    work_hours = 0
    if check_in and check_out:
        # Simple calc assuming same day
        in_time = datetime.strptime(check_in, "%H:%M")
        out_time = datetime.strptime(check_out, "%H:%M")
        diff = (out_time - in_time).total_seconds() / 3600
        work_hours = round(max(diff, 0), 1)
        
    att = Attendance(
        tenant_id=g.tenant_id,
        employee_id=data["employee_id"],
        date=data["date"],
        check_in=check_in,
        check_out=check_out,
        work_hours=work_hours,
        status=data.get("status", "PRESENT"),
        note=data.get("note")
    )
    db.session.add(att)
    db.session.commit()
    return jsonify({"message": "Thêm thành công"}), 201

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
            r.check_in.strftime("%H:%M") if r.check_in else "",
            r.check_out.strftime("%H:%M") if r.check_out else "",
            r.work_hours or 0,
            r.status,
            r.note or ""
        ])
        
    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendance_{month}_{year}.csv"}
    )
