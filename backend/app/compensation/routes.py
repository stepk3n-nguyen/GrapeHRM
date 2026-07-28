"""
Blueprint Compensation — cấu hình lương, gán lương, chạy bảng lương, phiếu lương.
"""

from datetime import datetime, date, timedelta, timezone

from flask import request, jsonify, g, Response
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.extensions import db
from app.models.employee import Employee
from app.models.user import User
from app.models.compensation import (
    SalaryStructure, SalaryAllowance, SalaryDeduction, EmployeeSalary,
    PayrollRun, Payslip, PayslipItem, OvertimeRequest
)
from app.models.leave import LeaveRequest
from sqlalchemy import or_, and_, extract
from app.services.payroll_service import run_payroll
from app.services.audit_service import log_action
from . import compensation_bp


def _current_employee_id():
    user = User.query.get(int(get_jwt_identity()))
    return user.employee_id if user else None


def _is_hr_admin():
    return get_jwt().get("role") in ["super_admin", "admin", "hr_manager"]


def _guard():
    if not _is_hr_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403
    return None


# ── Cấu hình lương generic (structures / allowances / deductions) ───────
def _list(model, fields):
    block = _guard()
    if block:
        return block
    items = model.query.filter_by(tenant_id=g.tenant_id).all()
    return jsonify([{f: (float(getattr(i, f)) if f in ("basic_salary", "default_amount") else getattr(i, f)) for f in fields} for i in items]), 200


@compensation_bp.route("/salary-structures", methods=["GET"])
@jwt_required()
def list_structures():
    return _list(SalaryStructure, ["id", "name", "basic_salary", "description"])


@compensation_bp.route("/salary-structures", methods=["POST"])
@jwt_required()
def create_structure():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    if not d.get("name"):
        return jsonify({"error": "Thiếu tên cấu trúc"}), 400
    s = SalaryStructure(tenant_id=g.tenant_id, name=d["name"], basic_salary=d.get("basic_salary", 0), description=d.get("description"))
    db.session.add(s); db.session.commit()
    return jsonify({"message": "Đã tạo", "id": s.id}), 201


@compensation_bp.route("/salary-structures/<int:sid>", methods=["PUT"])
@jwt_required()
def update_structure(sid):
    block = _guard()
    if block:
        return block
    s = SalaryStructure.query.filter_by(id=sid, tenant_id=g.tenant_id).first()
    if not s:
        return jsonify({"error": "Không tìm thấy"}), 404
    d = request.get_json(silent=True) or {}
    for f in ["name", "basic_salary", "description"]:
        if f in d:
            setattr(s, f, d[f])
    db.session.commit()
    return jsonify({"message": "Đã cập nhật"}), 200


@compensation_bp.route("/salary-structures/<int:sid>", methods=["DELETE"])
@jwt_required()
def delete_structure(sid):
    block = _guard()
    if block:
        return block
    s = SalaryStructure.query.filter_by(id=sid, tenant_id=g.tenant_id).first()
    if not s:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(s); db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


def _crud_amount(model, prefix):
    """Sinh sẵn 4 route CRUD cho allowance/deduction (cùng cấu trúc)."""
    @compensation_bp.route(f"/{prefix}", methods=["GET"], endpoint=f"list_{prefix}")
    @jwt_required()
    def _list_amt():
        return _list(model, ["id", "name", "type", "default_amount"])

    @compensation_bp.route(f"/{prefix}", methods=["POST"], endpoint=f"create_{prefix}")
    @jwt_required()
    def _create_amt():
        block = _guard()
        if block:
            return block
        d = request.get_json(silent=True) or {}
        if not d.get("name"):
            return jsonify({"error": "Thiếu tên"}), 400
        obj = model(tenant_id=g.tenant_id, name=d["name"], type=d.get("type", "FIXED"), default_amount=d.get("default_amount", 0))
        db.session.add(obj); db.session.commit()
        return jsonify({"message": "Đã tạo", "id": obj.id}), 201

    @compensation_bp.route(f"/{prefix}/<int:oid>", methods=["PUT"], endpoint=f"update_{prefix}")
    @jwt_required()
    def _update_amt(oid):
        block = _guard()
        if block:
            return block
        obj = model.query.filter_by(id=oid, tenant_id=g.tenant_id).first()
        if not obj:
            return jsonify({"error": "Không tìm thấy"}), 404
        d = request.get_json(silent=True) or {}
        for f in ["name", "type", "default_amount"]:
            if f in d:
                setattr(obj, f, d[f])
        db.session.commit()
        return jsonify({"message": "Đã cập nhật"}), 200

    @compensation_bp.route(f"/{prefix}/<int:oid>", methods=["DELETE"], endpoint=f"delete_{prefix}")
    @jwt_required()
    def _delete_amt(oid):
        block = _guard()
        if block:
            return block
        obj = model.query.filter_by(id=oid, tenant_id=g.tenant_id).first()
        if not obj:
            return jsonify({"error": "Không tìm thấy"}), 404
        db.session.delete(obj); db.session.commit()
        return jsonify({"message": "Đã xóa"}), 200


_crud_amount(SalaryAllowance, "salary-allowances")
_crud_amount(SalaryDeduction, "salary-deductions")


# ── Mức lương nhân viên ─────────────────────────────────────────────────
@compensation_bp.route("/employee-salaries", methods=["GET"])
@jwt_required()
def list_employee_salaries():
    """Tất cả NV đang làm + mức lương hiện hành (cho trang gán lương)."""
    block = _guard()
    if block:
        return block
    today = date.today()
    employees = Employee.query.filter_by(tenant_id=g.tenant_id, state="ACTIVE").all()
    res = []
    for e in employees:
        cur = (EmployeeSalary.query
               .filter(EmployeeSalary.employee_id == e.id, EmployeeSalary.effective_date <= today)
               .filter((EmployeeSalary.end_date.is_(None)) | (EmployeeSalary.end_date >= today))
               .order_by(EmployeeSalary.effective_date.desc()).first())
        res.append({
            "employee_id": e.id,
            "employee_code": e.employee_id,
            "employee_name": e.full_name(),
            "current_salary": float(cur.basic_salary) if cur else None,
            "effective_date": cur.effective_date.isoformat() if cur else None,
        })
    return jsonify(res), 200


@compensation_bp.route("/employee-salaries/<int:emp_id>", methods=["GET"])
@jwt_required()
def salary_history(emp_id):
    block = _guard()
    if block:
        return block
    rows = EmployeeSalary.query.filter_by(tenant_id=g.tenant_id, employee_id=emp_id).order_by(EmployeeSalary.effective_date.desc()).all()
    return jsonify([{
        "id": r.id, "basic_salary": float(r.basic_salary),
        "effective_date": r.effective_date.isoformat(),
        "end_date": r.end_date.isoformat() if r.end_date else None,
        "note": r.note,
    } for r in rows]), 200


@compensation_bp.route("/employee-salaries", methods=["POST"])
@jwt_required()
def assign_salary():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    emp_id = d.get("employee_id")
    emp = Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first()
    if not emp:
        return jsonify({"error": "Nhân viên không hợp lệ"}), 400
    try:
        eff = datetime.strptime(str(d.get("effective_date")), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Ngày hiệu lực không hợp lệ"}), 400
    if d.get("basic_salary") in (None, ""):
        return jsonify({"error": "Thiếu lương cơ bản"}), 400

    # Đóng mức lương đang mở trước đó để giữ lịch sử
    prev = (EmployeeSalary.query
            .filter(EmployeeSalary.employee_id == emp_id, EmployeeSalary.end_date.is_(None))
            .order_by(EmployeeSalary.effective_date.desc()).first())
    if prev and prev.effective_date < eff:
        prev.end_date = eff - timedelta(days=1)

    row = EmployeeSalary(
        tenant_id=g.tenant_id, employee_id=emp_id,
        structure_id=d.get("structure_id"),
        basic_salary=d["basic_salary"], effective_date=eff, note=d.get("note"),
    )
    db.session.add(row)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Đã tồn tại mức lương cho ngày hiệu lực này"}), 400
    return jsonify({"message": "Đã gán mức lương", "id": row.id}), 201


# ── Bảng lương (payroll runs) ───────────────────────────────────────────
@compensation_bp.route("/payroll", methods=["GET"])
@jwt_required()
def list_payroll():
    block = _guard()
    if block:
        return block
    q = PayrollRun.query.filter_by(tenant_id=g.tenant_id)
    year = request.args.get("year")
    if year:
        q = q.filter_by(year=int(year))
    runs = q.order_by(PayrollRun.year.desc(), PayrollRun.month.desc()).all()
    return jsonify([{
        "id": r.id, "month": r.month, "year": r.year, "status": r.status,
        "total_amount": float(r.total_amount), "payslip_count": len(r.payslips),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in runs]), 200


@compensation_bp.route("/payroll/run", methods=["POST"])
@jwt_required()
def run_payroll_route():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    try:
        month = int(d.get("month")); year = int(d.get("year"))
    except (TypeError, ValueError):
        return jsonify({"error": "Thiếu tháng/năm"}), 400
    if not (1 <= month <= 12):
        return jsonify({"error": "Tháng không hợp lệ"}), 400

    run, err = run_payroll(g.tenant_id, month, year, int(get_jwt_identity()))
    if err:
        return jsonify({"error": err}), 400

    from app.services.audit_service import log_action
    log_action("RUN", "PAYROLL", run.id, details={"month": month, "year": year, "total": float(run.total_amount)})
    db.session.commit()

    pending_leaves, pending_ot = _count_pending_requests(g.tenant_id, month, year)

    return jsonify({
        "message": "Đã chạy bảng lương",
        "id": run.id,
        "payslip_count": len(run.payslips),
        "total_amount": float(run.total_amount),
        "pending_leave": pending_leaves,
        "pending_overtime": pending_ot
    }), 200


def _serialize_payslip(ps, detail=False):
    base = {
        "id": ps.id, "employee_id": ps.employee_id,
        "employee_name": ps.employee.full_name() if ps.employee else "?",
        "employee_code": ps.employee.employee_id if ps.employee else None,
        "basic_salary": float(ps.basic_salary),
        "total_work_days": float(ps.total_work_days),
        "standard_work_days": ps.standard_work_days,
        "total_leave_days": float(ps.total_leave_days or 0),
        "total_unpaid_leave": float(ps.total_unpaid_leave or 0),
        "total_allowances": float(ps.total_allowances or 0),
        "total_deductions": float(ps.total_deductions or 0),
        "overtime_hours": float(ps.overtime_hours or 0),
        "overtime_pay": float(ps.overtime_pay or 0),
        "gross_salary": float(ps.gross_salary or 0),
        "num_dependents": ps.num_dependents or 0,
        "taxable_income": float(ps.taxable_income or 0),
        "personal_income_tax": float(ps.personal_income_tax or 0),
        "net_salary": float(ps.net_salary),
    }
    if detail:
        base["items"] = [{"item_type": it.item_type, "name": it.name, "amount": float(it.amount)} for it in ps.items]
    return base


@compensation_bp.route("/payroll/<int:run_id>", methods=["GET"])
@jwt_required()
def get_payroll(run_id):
    block = _guard()
    if block:
        return block
    run = PayrollRun.query.filter_by(id=run_id, tenant_id=g.tenant_id).first()
    if not run:
        return jsonify({"error": "Không tìm thấy"}), 404
    from app.models.tenant import Tenant
    tenant = Tenant.query.get(g.tenant_id)
    return jsonify({
        "id": run.id, "month": run.month, "year": run.year, "status": run.status,
        "company_name": tenant.name if tenant else None,
        "total_amount": float(run.total_amount),
        "payslips": [_serialize_payslip(p, detail=True) for p in run.payslips],
    }), 200


def _count_pending_requests(tenant_id, month, year):
    # Check LeaveRequest (PENDING_HR and overlaps with month/year)
    pending_leaves = LeaveRequest.query.filter(
        LeaveRequest.tenant_id == tenant_id,
        LeaveRequest.status == "PENDING_HR",
        or_(
            and_(extract('year', LeaveRequest.start_date) == year, extract('month', LeaveRequest.start_date) == month),
            and_(extract('year', LeaveRequest.end_date) == year, extract('month', LeaveRequest.end_date) == month)
        )
    ).count()

    # Check OvertimeRequest (PENDING and exactly in month/year)
    pending_ot = OvertimeRequest.query.filter(
        OvertimeRequest.tenant_id == tenant_id,
        OvertimeRequest.status == "PENDING",
        extract('year', OvertimeRequest.date) == year,
        extract('month', OvertimeRequest.date) == month
    ).count()

    return pending_leaves, pending_ot


@compensation_bp.route("/payroll/<int:run_id>/check-pending", methods=["GET"])
@jwt_required()
def check_pending_for_payroll(run_id):
    block = _guard()
    if block:
        return block
    run = PayrollRun.query.filter_by(id=run_id, tenant_id=g.tenant_id).first()
    if not run:
        return jsonify({"error": "Không tìm thấy"}), 404
        
    pending_leaves, pending_ot = _count_pending_requests(g.tenant_id, run.month, run.year)

    return jsonify({
        "pending_leave": pending_leaves,
        "pending_overtime": pending_ot
    }), 200


@compensation_bp.route("/payroll/<int:run_id>/confirm", methods=["PUT"])
@jwt_required()
def confirm_payroll(run_id):
    block = _guard()
    if block:
        return block
    run = PayrollRun.query.filter_by(id=run_id, tenant_id=g.tenant_id).first()
    if not run:
        return jsonify({"error": "Không tìm thấy"}), 404
    if run.status != "DRAFT":
        return jsonify({"error": "Chỉ xác nhận được đợt đang ở trạng thái nháp"}), 400
    run.status = "CONFIRMED"
    run.confirmed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"message": "Đã xác nhận đợt lương"}), 200


@compensation_bp.route("/payroll/<int:run_id>/lock", methods=["PUT"])
@jwt_required()
def lock_payroll(run_id):
    block = _guard()
    if block:
        return block
    run = PayrollRun.query.filter_by(id=run_id, tenant_id=g.tenant_id).first()
    if not run:
        return jsonify({"error": "Không tìm thấy"}), 404
    if run.status != "CONFIRMED":
        return jsonify({"error": "Chỉ khóa được đợt đã xác nhận"}), 400
    run.status = "LOCKED"
    db.session.commit()
    return jsonify({"message": "Đã khóa đợt lương"}), 200


# ── Phiếu lương cá nhân ─────────────────────────────────────────────────
def _my_payslip(month, year):
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.employee_id:
        return None, None
    run = PayrollRun.query.filter_by(tenant_id=g.tenant_id, month=month, year=year).first()
    if not run or run.status == "DRAFT":
        return run, None
    ps = Payslip.query.filter_by(payroll_id=run.id, employee_id=user.employee_id).first()
    return run, ps


@compensation_bp.route("/payslips/me", methods=["GET"])
@jwt_required()
def my_payslip():
    try:
        month = int(request.args.get("month")); year = int(request.args.get("year"))
    except (TypeError, ValueError):
        return jsonify({"error": "Thiếu tháng/năm"}), 400
    run, ps = _my_payslip(month, year)
    if not ps:
        return jsonify({"error": "Chưa có phiếu lương đã xác nhận cho kỳ này"}), 404
    return jsonify({"month": month, "year": year, **_serialize_payslip(ps, detail=True)}), 200


@compensation_bp.route("/payslips/<int:ps_id>/export-pdf", methods=["GET"])
@jwt_required()
def export_payslip_pdf(ps_id):
    ps = Payslip.query.get(ps_id)
    if not ps:
        return jsonify({"error": "Không tìm thấy"}), 404
    run = PayrollRun.query.get(ps.payroll_id)
    # Cách ly tenant + quyền: HR xem mọi phiếu, NV chỉ phiếu của mình
    if not run or run.tenant_id != g.tenant_id:
        return jsonify({"error": "Không tìm thấy"}), 404
    if not _is_hr_admin():
        user = User.query.get(int(get_jwt_identity()))
        if not user or user.employee_id != ps.employee_id:
            return jsonify({"error": "Không có quyền"}), 403

    try:
        from app.services.payslip_pdf import build_payslip_pdf
        pdf = build_payslip_pdf(ps, ps.employee, run)
    except ImportError:
        return jsonify({"error": "Thiếu thư viện reportlab. Chạy: pip install reportlab"}), 500

    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment;filename=payslip_{run.month}_{run.year}.pdf"})


# ════════════════════════════════════════════════════════════════════════
# TĂNG CA (OVERTIME)
# ════════════════════════════════════════════════════════════════════════

_OT_LABEL = {"WEEKDAY": "Ngày thường (150%)", "WEEKEND": "Cuối tuần (200%)", "HOLIDAY": "Ngày lễ (300%)"}


def _serialize_ot(o):
    return {
        "id": o.id, "employee_id": o.employee_id,
        "employee_name": o.employee.full_name() if o.employee else "?",
        "date": o.date.isoformat(), "hours": float(o.hours),
        "ot_type": o.ot_type, "ot_type_label": _OT_LABEL.get(o.ot_type, o.ot_type),
        "multiplier": o.multiplier, "reason": o.reason, "status": o.status,
    }


@compensation_bp.route("/overtime", methods=["GET"])
@jwt_required()
def list_overtime():
    """HR xem tất cả; nhân viên chỉ xem đơn của mình. Lọc ?month=&year=&status=."""
    q = OvertimeRequest.query.filter_by(tenant_id=g.tenant_id)
    if not _is_hr_admin():
        emp_id = _current_employee_id()
        if not emp_id:
            return jsonify([]), 200
        q = q.filter_by(employee_id=emp_id)
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    status = request.args.get("status")
    if month:
        q = q.filter(db.extract("month", OvertimeRequest.date) == month)
    if year:
        q = q.filter(db.extract("year", OvertimeRequest.date) == year)
    if status:
        q = q.filter_by(status=status)
    items = q.order_by(OvertimeRequest.date.desc()).all()
    return jsonify([_serialize_ot(o) for o in items]), 200


@compensation_bp.route("/overtime", methods=["POST"])
@jwt_required()
def create_overtime():
    """Nhân viên đăng ký tăng ca cho CHÍNH MÌNH (server lấy employee từ token)."""
    d = request.get_json(silent=True) or {}
    
    if _is_hr_admin() and d.get("employee_id"):
        emp_id = d.get("employee_id")
        from app.models.employee import Employee
        emp = Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first()
        if not emp:
            return jsonify({"error": "Nhân viên không tồn tại"}), 400
    else:
        emp_id = _current_employee_id()
        
    if not emp_id:
        return jsonify({"error": "Tài khoản chưa gắn hồ sơ nhân viên"}), 400

    try:
        ot_date = datetime.strptime(d["date"], "%Y-%m-%d").date()
        hours = float(d["hours"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Thiếu hoặc sai ngày/số giờ"}), 400
    if hours <= 0 or hours > 12:
        return jsonify({"error": "Số giờ tăng ca phải trong khoảng 0–12"}), 400
    ot_type = d.get("ot_type", "WEEKDAY")
    if ot_type not in ("WEEKDAY", "WEEKEND", "HOLIDAY"):
        return jsonify({"error": "Loại tăng ca không hợp lệ"}), 400

    o = OvertimeRequest(tenant_id=g.tenant_id, employee_id=emp_id, date=ot_date,
                        hours=hours, ot_type=ot_type, reason=d.get("reason"), status="PENDING")
    db.session.add(o)
    db.session.commit()
    return jsonify({"message": "Đã gửi đơn tăng ca", "id": o.id}), 201


@compensation_bp.route("/overtime/<int:oid>", methods=["PUT"])
@jwt_required()
def update_overtime(oid):
    """HR sửa đơn tăng ca của nhân viên."""
    block = _guard()
    if block:
        return block
    o = OvertimeRequest.query.filter_by(id=oid, tenant_id=g.tenant_id).first()
    if not o:
        return jsonify({"error": "Không tìm thấy"}), 404
        
    d = request.get_json(silent=True) or {}
    
    if "date" in d:
        try:
            o.date = datetime.strptime(d["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Ngày không hợp lệ"}), 400
            
    if "hours" in d:
        try:
            h = float(d["hours"])
            if h <= 0 or h > 12:
                return jsonify({"error": "Số giờ phải trong khoảng 0-12"}), 400
            o.hours = h
        except ValueError:
            return jsonify({"error": "Số giờ không hợp lệ"}), 400
            
    if "ot_type" in d:
        if d["ot_type"] in ("WEEKDAY", "WEEKEND", "HOLIDAY"):
            o.ot_type = d["ot_type"]
            
    if "reason" in d:
        o.reason = d["reason"]
        
    if "employee_id" in d:
        emp = Employee.query.filter_by(id=d["employee_id"], tenant_id=g.tenant_id).first()
        if not emp:
            return jsonify({"error": "Nhân viên không tồn tại"}), 400
        o.employee_id = emp.id
        
    db.session.commit()
    return jsonify({"message": "Đã cập nhật đơn tăng ca"}), 200

@compensation_bp.route("/overtime/<int:oid>/approve", methods=["PUT"])
@jwt_required()
def approve_overtime(oid):
    block = _guard()
    if block:
        return block
    o = OvertimeRequest.query.filter_by(id=oid, tenant_id=g.tenant_id).first()
    if not o:
        return jsonify({"error": "Không tìm thấy"}), 404
    if o.status != "PENDING":
        return jsonify({"error": "Đơn không ở trạng thái chờ duyệt"}), 400
    o.status = "APPROVED"
    log_action("APPROVE", "OVERTIME", o.id)
    db.session.commit()
    return jsonify({"message": "Đã duyệt tăng ca"}), 200


@compensation_bp.route("/overtime/<int:oid>/reject", methods=["PUT"])
@jwt_required()
def reject_overtime(oid):
    block = _guard()
    if block:
        return block
    o = OvertimeRequest.query.filter_by(id=oid, tenant_id=g.tenant_id).first()
    if not o:
        return jsonify({"error": "Không tìm thấy"}), 404
    o.status = "REJECTED"
    log_action("REJECT", "OVERTIME", o.id)
    db.session.commit()
    return jsonify({"message": "Đã từ chối tăng ca"}), 200


@compensation_bp.route("/overtime/<int:oid>", methods=["DELETE"])
@jwt_required()
def delete_overtime(oid):
    """Nhân viên tự hủy đơn đang chờ của mình; HR xóa được mọi đơn."""
    o = OvertimeRequest.query.filter_by(id=oid, tenant_id=g.tenant_id).first()
    if not o:
        return jsonify({"error": "Không tìm thấy"}), 404
    if not _is_hr_admin():
        if o.employee_id != _current_employee_id() or o.status != "PENDING":
            return jsonify({"error": "Chỉ hủy được đơn đang chờ của chính bạn"}), 403
    db.session.delete(o)
    db.session.commit()
    return jsonify({"message": "Đã xóa đơn tăng ca"}), 200
