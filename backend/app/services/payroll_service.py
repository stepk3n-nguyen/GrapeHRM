"""
Logic tính lương — chạy bảng lương cho 1 tháng/năm của 1 tenant.

Số ngày công KHÔNG tính riêng ở đây — dùng chung attendance_service.monthly_summary
(một nguồn sự thật duy nhất với màn hình Tổng công tháng), tránh 2 nơi ra 2 số khác nhau.
Ngày công chuẩn = số ngày làm việc (T2–T6) trong tháng, đã loại ngày lễ có lương.
"""

import calendar
from datetime import date

from sqlalchemy import extract

from app.extensions import db
from app.models.employee import Employee
from app.models.compensation import (
    SalaryAllowance, SalaryDeduction, EmployeeSalary, PayrollRun, Payslip, PayslipItem,
    OvertimeRequest
)
from app.services.calendar_service import count_standard_working_days
from app.services.attendance_service import monthly_summary
from app.services.tax_service import compute_pit


def compute_overtime(emp_id, year, month, basic, standard_days):
    """Tổng giờ + tiền tăng ca đã DUYỆT trong tháng.
    Lương giờ = lương cơ bản / (số ngày công chuẩn × 8). Tiền OT = giờ × lương giờ × hệ số."""
    reqs = OvertimeRequest.query.filter(
        OvertimeRequest.employee_id == emp_id,
        OvertimeRequest.status == "APPROVED",
        extract("year", OvertimeRequest.date) == year,
        extract("month", OvertimeRequest.date) == month,
    ).all()
    if not reqs:
        return 0.0, 0.0
    hourly = float(basic) / (max(standard_days, 1) * 8)
    total_hours = 0.0
    total_pay = 0.0
    for r in reqs:
        h = float(r.hours)
        total_hours += h
        total_pay += hourly * h * r.multiplier
    return total_hours, total_pay


def get_effective_salary(emp_id, year, month):
    """Mức lương đang hiệu lực vào cuối tháng tính lương."""
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    return (EmployeeSalary.query
            .filter(EmployeeSalary.employee_id == emp_id,
                    EmployeeSalary.effective_date <= month_end)
            .filter((EmployeeSalary.end_date.is_(None)) | (EmployeeSalary.end_date >= month_end))
            .order_by(EmployeeSalary.effective_date.desc())
            .first())


def run_payroll(tenant_id, month, year, created_by):
    """Chạy (hoặc chạy lại nếu DRAFT) bảng lương. Trả về (run, error)."""
    run = PayrollRun.query.filter_by(tenant_id=tenant_id, month=month, year=year).first()
    if run and run.status == "LOCKED":
        return None, "Đợt lương đã khóa, không thể chạy lại"
    if run and run.status == "CONFIRMED":
        return None, "Đợt lương đã xác nhận. Hãy mở lại (chưa hỗ trợ) hoặc chọn tháng khác"

    if run:
        for ps in list(run.payslips):
            db.session.delete(ps)
        db.session.flush()
    else:
        run = PayrollRun(tenant_id=tenant_id, month=month, year=year, status="DRAFT", created_by=created_by)
        db.session.add(run)
        db.session.flush()

    standard = count_standard_working_days(tenant_id, year, month) or 1
    allowances = SalaryAllowance.query.filter_by(tenant_id=tenant_id).all()
    deductions = SalaryDeduction.query.filter_by(tenant_id=tenant_id).all()
    employees = Employee.query.filter_by(tenant_id=tenant_id, state="ACTIVE").all()

    # Tổng công tháng — MỘT nguồn sự thật (dùng chung với màn hình Tổng công)
    summary_by_emp = {r["employee_id"]: r for r in monthly_summary(tenant_id, year, month)}

    grand_total = 0.0
    for emp in employees:
        sal = get_effective_salary(emp.id, year, month)
        if not sal:
            continue  # bỏ qua NV chưa được gán mức lương
        basic = float(sal.basic_salary)

        s = summary_by_emp.get(emp.id) or {}
        # Ngày công thực = ngày đủ công + 0.5 × (nửa công + thiếu chấm ra)
        work_days = (s.get("full_days", 0)
                     + 0.5 * s.get("half_days", 0)
                     + 0.5 * s.get("missing_checkout", 0))
        paid_leave = s.get("paid_leave", 0.0)
        unpaid_leave = s.get("unpaid_leave", 0.0)

        paid_days = work_days + paid_leave
        ratio = min(paid_days / standard, 1.0)
        actual = basic * ratio  # lương cơ bản theo ngày công thực tế

        total_allow = 0.0
        total_deduct = 0.0  # BH bắt buộc
        items = []
        for a in allowances:
            amt = float(a.default_amount) if a.type == "FIXED" else basic * float(a.default_amount) / 100.0
            total_allow += amt
            items.append(("ALLOWANCE", a.name, round(amt, 2)))
        for d in deductions:
            amt = float(d.default_amount) if d.type == "FIXED" else basic * float(d.default_amount) / 100.0
            total_deduct += amt
            items.append(("DEDUCTION", d.name, round(amt, 2)))

        # ── Tăng ca: tiền OT = (lương giờ) × giờ × hệ số ───────────────
        ot_hours, ot_pay = compute_overtime(emp.id, year, month, basic, standard)
        if ot_pay > 0:
            items.append(("ALLOWANCE", f"Tăng ca ({ot_hours:g} giờ)", round(ot_pay, 2)))

        # ── Thu nhập chịu thuế & thuế TNCN ────────────────────────────
        gross = actual + total_allow + ot_pay
        ti, pit = compute_pit(gross, total_deduct, emp.num_dependents or 0)
        if pit > 0:
            items.append(("DEDUCTION", "Thuế TNCN", round(pit, 2)))

        net = gross - total_deduct - pit

        ps = Payslip(
            payroll_id=run.id, employee_id=emp.id, basic_salary=round(basic, 2),
            total_work_days=work_days, standard_work_days=standard,
            total_leave_days=paid_leave, total_unpaid_leave=unpaid_leave,
            total_allowances=round(total_allow, 2), total_deductions=round(total_deduct, 2),
            overtime_hours=round(ot_hours, 1), overtime_pay=round(ot_pay, 2),
            gross_salary=round(gross, 2), num_dependents=emp.num_dependents or 0,
            taxable_income=round(ti, 2), personal_income_tax=round(pit, 2),
            net_salary=round(net, 2),
        )
        db.session.add(ps)
        db.session.flush()
        for it, nm, am in items:
            db.session.add(PayslipItem(payslip_id=ps.id, item_type=it, name=nm, amount=am))
        grand_total += net

    run.total_amount = round(grand_total, 2)
    run.status = "DRAFT"
    db.session.commit()
    return run, None
