"""
Kịch bản demo GrapeHRM — tạo dữ liệu thực tế để test.

Chạy từ thư mục backend:
    python seed_demo.py

Tạo:
  • 2 phòng ban, 3 chức vụ, 3 cấu trúc lương
  • 5 nhân viên + tài khoản đăng nhập
  • Chấm công tháng 5 và 6/2026 (có PRESENT / LATE / ABSENT / ON_LEAVE)
  • 5 đơn nghỉ phép với các trạng thái khác nhau
  • Mức lương được gán sẵn (để chạy payroll ngay)

An toàn khi chạy lại nhiều lần (ON DUPLICATE KEY / first-or-create).
"""

import sys
import os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, time, timedelta
from app import create_app
from app.extensions import db

app = create_app("development")

with app.app_context():
    from app.models.employee import Employee, JobTitle, Department, EmployeeSequence
    from app.models.user import User
    from app.models.leave import (
        LeaveType, LeavePolicy, EmployeeLeavePolicy,
        LeaveRequest, LeaveApprovalLog,
    )
    from app.models.attendance import Attendance
    from app.models.work import WorkShift
    from app.models.compensation import SalaryStructure, EmployeeSalary
    from app.models.tenant import Tenant

    tenant = Tenant.query.filter_by(slug="grapecorp").first()
    if not tenant:
        print("❌  Không tìm thấy tenant 'grapecorp'. Chạy 'python run.py' trước.")
        sys.exit(1)

    TID = tenant.id
    admin_user = User.query.filter_by(tenant_id=TID, username="admin").first()
    YEAR = 2026
    TODAY = date(2026, 6, 17)

    print("🔧 Tạo dữ liệu demo GrapeHRM...\n")

    # ────────────────────────────────────────────────────────────────────
    # 1. PHÒNG BAN
    # ────────────────────────────────────────────────────────────────────
    def _dept(name, desc=""):
        d = Department.query.filter_by(tenant_id=TID, name=name).first()
        if not d:
            d = Department(tenant_id=TID, name=name, description=desc)
            db.session.add(d)
            db.session.flush()
            print(f"  ✓ Phòng ban: {name}")
        return d

    dept_it   = _dept("Phòng Công nghệ", "Software & System")
    dept_sale = _dept("Phòng Kinh doanh", "Sales & Marketing")
    db.session.commit()

    # ────────────────────────────────────────────────────────────────────
    # 2. CHỨC VỤ
    # ────────────────────────────────────────────────────────────────────
    def _title(name):
        t = JobTitle.query.filter_by(tenant_id=TID, name=name).first()
        if not t:
            t = JobTitle(tenant_id=TID, name=name)
            db.session.add(t)
            db.session.flush()
            print(f"  ✓ Chức vụ: {name}")
        return t

    title_mgr  = _title("Trưởng phòng")
    title_dev  = _title("Lập trình viên")
    title_sale = _title("Nhân viên kinh doanh")
    db.session.commit()

    # ────────────────────────────────────────────────────────────────────
    # 3. CẤU TRÚC LƯƠNG
    # ────────────────────────────────────────────────────────────────────
    def _struct(name, basic):
        s = SalaryStructure.query.filter_by(tenant_id=TID, name=name).first()
        if not s:
            s = SalaryStructure(tenant_id=TID, name=name, basic_salary=basic)
            db.session.add(s)
            db.session.flush()
            print(f"  ✓ Cấu trúc lương: {name} ({basic:,.0f} đ)")
        return s

    struct_mgr  = _struct("Lương Trưởng phòng",      20_000_000)
    struct_dev  = _struct("Lương Lập trình viên",     15_000_000)
    struct_sale = _struct("Lương Kinh doanh",         12_000_000)
    db.session.commit()

    # ── Địa điểm làm việc demo (geofence) — sửa lại bằng "Lấy vị trí hiện tại" tại VP ──
    from app.models.work import WorkLocation
    if WorkLocation.query.filter_by(tenant_id=TID).count() == 0:
        db.session.add(WorkLocation(
            tenant_id=TID, name="Văn phòng chính",
            latitude=20.992697, longitude=105.779162,
            radius_meters=300, is_active=True,
        ))
        db.session.commit()
        print("  ✓ Địa điểm làm việc demo (bán kính 300m)")
    print()

    # ── Ca làm việc: ngoài ca hành chính mặc định, thêm ca sớm để demo nhiều ca ──
    default_shift = WorkShift.query.filter_by(tenant_id=TID, is_default=True).first()
    early_shift = WorkShift.query.filter_by(tenant_id=TID, name="Ca sớm").first()
    if not early_shift:
        early_shift = WorkShift(
            tenant_id=TID, name="Ca sớm",
            start_time=time(7, 0), end_time=time(16, 0),
            late_threshold_minutes=10, break_minutes=60, is_default=False,
        )
        db.session.add(early_shift)
        db.session.commit()
        print("  ✓ Ca sớm (07:00-16:00) — demo nhiều ca")

    # ────────────────────────────────────────────────────────────────────
    # 4. NHÂN VIÊN + USER + GÁN LƯƠNG + GÁN CHÍNH SÁCH PHÉP
    # ────────────────────────────────────────────────────────────────────
    policy = LeavePolicy.query.filter_by(tenant_id=TID, is_default=True).first()

    seq = EmployeeSequence.query.filter_by(tenant_id=TID).first()
    if not seq:
        seq = EmployeeSequence(tenant_id=TID, current_value=0)
        db.session.add(seq)
        db.session.flush()

    specs = [
        dict(
            first_name="Nguyễn Văn", last_name="An",
            gender=1, birthday=date(1988, 3, 15),
            mobile="0901234001", work_email="an.nv@grapecorp.com",
            joined_date=date(2022, 1, 10), dept=dept_it, title=title_mgr,
            username="an.nv", role="hr_manager",
            struct=struct_mgr, basic=20_000_000, dependents=2,
        ),
        dict(
            first_name="Trần Thị", last_name="Bình",
            gender=2, birthday=date(1996, 7, 22),
            mobile="0901234002", work_email="binh.tt@grapecorp.com",
            joined_date=date(2023, 3, 1), dept=dept_it, title=title_dev,
            username="binh.tt", role="employee",
            struct=struct_dev, basic=15_000_000, dependents=1,
        ),
        dict(
            first_name="Lê Văn", last_name="Cường",
            gender=1, birthday=date(1995, 11, 5),
            mobile="0901234003", work_email="cuong.lv@grapecorp.com",
            joined_date=date(2022, 8, 15), dept=dept_it, title=title_dev,
            username="cuong.lv", role="employee",
            struct=struct_dev, basic=14_000_000,
        ),
        dict(
            first_name="Phạm Thị", last_name="Dung",
            gender=2, birthday=date(1997, 4, 30),
            mobile="0901234004", work_email="dung.pt@grapecorp.com",
            joined_date=date(2023, 6, 1), dept=dept_sale, title=title_sale,
            username="dung.pt", role="employee",
            struct=struct_sale, basic=12_000_000,
        ),
        dict(
            first_name="Hoàng Văn", last_name="Em",
            gender=1, birthday=date(1999, 1, 18),
            mobile="0901234005", work_email="em.hv@grapecorp.com",
            joined_date=date(2024, 2, 1), dept=dept_sale, title=title_sale,
            username="em.hv", role="employee",
            struct=struct_sale, basic=11_000_000,
        ),
    ]

    print("👥 Tạo nhân viên...")
    emps = {}
    for sp in specs:
        emp = Employee.query.filter_by(tenant_id=TID, work_email=sp["work_email"]).first()
        if not emp:
            seq.current_value += 1
            emp = Employee(
                tenant_id=TID,
                employee_id=f"NV-{seq.current_value:03d}",
                first_name=sp["first_name"],
                last_name=sp["last_name"],
                gender=sp["gender"],
                birthday=sp["birthday"],
                mobile=sp["mobile"],
                work_email=sp["work_email"],
                joined_date=sp["joined_date"],
                state="ACTIVE",
                title_id=sp["title"].id,
                department_id=sp["dept"].id,
                num_dependents=sp.get("dependents", 0),
            )
            db.session.add(emp)
            db.session.flush()
            print(f"  ✓ {emp.employee_id}  {emp.first_name} {emp.last_name}  ({sp['dept'].name})")

        # User account
        u = User.query.filter_by(tenant_id=TID, username=sp["username"]).first()
        if not u:
            u = User(
                tenant_id=TID, employee_id=emp.id,
                username=sp["username"], email=sp["work_email"],
                role=sp["role"], is_active=True,
            )
            u.set_password("Employee@123")
            db.session.add(u)

        # Chính sách phép
        if policy and not EmployeeLeavePolicy.query.filter_by(employee_id=emp.id, effective_year=YEAR).first():
            db.session.add(EmployeeLeavePolicy(
                tenant_id=TID, employee_id=emp.id,
                policy_id=policy.id, effective_year=YEAR,
            ))

        # Gán ca làm việc (Dung làm ca sớm — demo nhiều ca)
        if emp.shift_id is None:
            emp.shift_id = early_shift.id if sp["username"] == "dung.pt" else (default_shift.id if default_shift else None)

        # Mức lương
        if not EmployeeSalary.query.filter_by(employee_id=emp.id, effective_date=date(2026, 1, 1)).first():
            db.session.add(EmployeeSalary(
                tenant_id=TID, employee_id=emp.id,
                structure_id=sp["struct"].id,
                basic_salary=sp["basic"],
                effective_date=date(2026, 1, 1),
                note="Mức lương demo 2026",
            ))

        emps[sp["username"]] = emp

    db.session.commit()
    print()

    # ────────────────────────────────────────────────────────────────────
    # 5. ĐƠN NGHỈ PHÉP
    # ────────────────────────────────────────────────────────────────────
    def _ltype(code):
        return LeaveType.query.filter_by(tenant_id=TID, code=code).first()

    print("📋 Tạo đơn nghỉ phép...")
    leave_specs = [
        dict(emp=emps["an.nv"],    ltype=_ltype("ANNUAL"),
             start=date(2026, 5, 26), end=date(2026, 5, 28), days=3,
             reason="Đi du lịch gia đình",      status="APPROVED"),
        dict(emp=emps["binh.tt"],  ltype=_ltype("ANNUAL"),
             start=date(2026, 6, 2),  end=date(2026, 6, 5),  days=4,
             reason="Về thăm quê",              status="APPROVED"),
        dict(emp=emps["cuong.lv"], ltype=_ltype("SICK"),
             start=date(2026, 6, 10), end=date(2026, 6, 11), days=2,
             reason="Sốt cao, có giấy bác sĩ",  status="APPROVED"),
        dict(emp=emps["dung.pt"],  ltype=_ltype("UNPAID"),
             start=date(2026, 5, 20), end=date(2026, 5, 22), days=3,
             reason="Việc cá nhân",             status="REJECTED",
             rejection_reason="Giai đoạn cao điểm kinh doanh cuối tháng"),
        dict(emp=emps["em.hv"],    ltype=_ltype("WEDDING"),
             start=date(2026, 7, 6),  end=date(2026, 7, 8),  days=3,
             reason="Ngày cưới",                status="PENDING_HR"),
    ]

    ICONS = {"APPROVED": "✅", "REJECTED": "❌", "PENDING_HR": "⏳"}
    for ls in leave_specs:
        if LeaveRequest.query.filter_by(employee_id=ls["emp"].id, start_date=ls["start"]).first():
            continue
        lr = LeaveRequest(
            tenant_id=TID,
            employee_id=ls["emp"].id,
            leave_type_id=ls["ltype"].id,
            start_date=ls["start"], end_date=ls["end"],
            total_days=ls["days"], reason=ls["reason"],
            status=ls["status"],
            rejection_reason=ls.get("rejection_reason"),
        )
        db.session.add(lr)
        db.session.flush()

        if ls["status"] in ("APPROVED", "REJECTED") and admin_user:
            db.session.add(LeaveApprovalLog(
                request_id=lr.id, approver_id=admin_user.id,
                action="APPROVED" if ls["status"] == "APPROVED" else "REJECTED",
                comment=ls.get("rejection_reason") or "Đã duyệt",
            ))

        print(f"  {ICONS[ls['status']]}  {ls['emp'].last_name}: {ls['ltype'].name} "
              f"{ls['start']} → {ls['end']} ({ls['days']} ngày)")

    db.session.commit()
    print()

    # ────────────────────────────────────────────────────────────────────
    # 6. CHẤM CÔNG (T5 + T6 / 2026)
    # ────────────────────────────────────────────────────────────────────
    print("🕐 Tạo chấm công...")

    def weekdays(start: date, end: date):
        d, result = start, []
        while d <= end:
            if d.weekday() < 5:
                result.append(d)
            d += timedelta(days=1)
        return result

    # Ngày ON_LEAVE theo đơn đã duyệt
    on_leave = {
        emps["an.nv"].id:    set(weekdays(date(2026, 5, 26), date(2026, 5, 28))),
        emps["binh.tt"].id:  set(weekdays(date(2026, 6, 2),  date(2026, 6, 5))),
        emps["cuong.lv"].id: set(weekdays(date(2026, 6, 10), date(2026, 6, 11))),
    }
    # Ngày đi muộn
    late = {
        emps["cuong.lv"].id: {date(2026, 5, 7),  date(2026, 6, 3)},
        emps["dung.pt"].id:  {date(2026, 5, 15)},
        emps["an.nv"].id:    {date(2026, 6, 11)},
    }
    # Ngày vắng mặt
    absent = {
        emps["em.hv"].id: {date(2026, 5, 22), date(2026, 6, 5)},
    }
    # Ngày nửa ngày
    half_day = {
        emps["dung.pt"].id: {date(2026, 6, 15)},
    }

    all_emps = list(emps.values())
    att_start = date(2026, 5, 1)
    att_end   = TODAY - timedelta(days=1)  # đến hôm qua
    total_att = 0

    # Ngày lễ: không sinh chấm công (NV được nghỉ có lương, không đi làm)
    from app.models.holiday import Holiday
    holiday_set = {h.date for h in Holiday.query.filter_by(tenant_id=TID).all()}

    for day in weekdays(att_start, att_end):
        if day in holiday_set:
            continue
        for emp in all_emps:
            if Attendance.query.filter_by(tenant_id=TID, employee_id=emp.id, date=day).first():
                continue

            eid = emp.id

            if eid in on_leave and day in on_leave[eid]:
                att = Attendance(tenant_id=TID, employee_id=eid, date=day,
                                 status="ON_LEAVE", source="MANUAL",
                                 note="Nghỉ phép đã được duyệt")

            elif eid in absent and day in absent[eid]:
                att = Attendance(tenant_id=TID, employee_id=eid, date=day,
                                 status="ABSENT", source="MANUAL",
                                 note="Vắng không phép")

            elif eid in half_day and day in half_day[eid]:
                att = Attendance(tenant_id=TID, employee_id=eid, date=day,
                                 check_in=time(8, 30), check_out=time(12, 30),
                                 work_hours=4.0, status="HALF_DAY", source="MANUAL",
                                 note="Về sớm buổi chiều")

            elif eid in late and day in late[eid]:
                att = Attendance(tenant_id=TID, employee_id=eid, date=day,
                                 check_in=time(9, 15), check_out=time(18, 0),
                                 work_hours=7.75, status="LATE", late_minutes=45,
                                 source="MANUAL", note="Đến muộn")

            else:
                att = Attendance(tenant_id=TID, employee_id=eid, date=day,
                                 check_in=time(8, 30), check_out=time(17, 30),
                                 work_hours=8.0, status="PRESENT", source="MANUAL")

            db.session.add(att)
            total_att += 1

    db.session.commit()
    print(f"  ✓ {total_att} bản ghi chấm công (01/05 → {att_end.strftime('%d/%m')}/2026)\n")

    # ────────────────────────────────────────────────────────────────────
    # 6b. ĐƠN TĂNG CA T5/2026 (đã duyệt — cộng vào bảng lương T5)
    # ────────────────────────────────────────────────────────────────────
    from app.models.compensation import OvertimeRequest

    ot_specs = [
        dict(emp=emps["binh.tt"],  date=date(2026, 5, 8),  hours=2, ot_type="WEEKDAY"),
        dict(emp=emps["binh.tt"],  date=date(2026, 5, 16), hours=3, ot_type="WEEKEND"),
        dict(emp=emps["cuong.lv"], date=date(2026, 5, 22), hours=2, ot_type="WEEKDAY"),
    ]
    ot_count = 0
    for o in ot_specs:
        if not OvertimeRequest.query.filter_by(tenant_id=TID, employee_id=o["emp"].id, date=o["date"]).first():
            db.session.add(OvertimeRequest(
                tenant_id=TID, employee_id=o["emp"].id, date=o["date"],
                hours=o["hours"], ot_type=o["ot_type"],
                reason="Hoàn thành tính năng gấp", status="APPROVED",
            ))
            ot_count += 1
    db.session.commit()
    if ot_count:
        print(f"  ✓ {ot_count} đơn tăng ca đã duyệt (T5/2026)\n")

    # ────────────────────────────────────────────────────────────────────
    # 7. CHẠY & XÁC NHẬN BẢNG LƯƠNG THÁNG 5/2026 (để demo phiếu lương sẵn)
    # ────────────────────────────────────────────────────────────────────
    from app.models.compensation import PayrollRun
    from app.services.payroll_service import run_payroll

    if not PayrollRun.query.filter_by(tenant_id=TID, month=5, year=2026).first():
        run, err = run_payroll(TID, 5, 2026, created_by=admin_user.id if admin_user else None)
        if run:
            run.status = "CONFIRMED"
            from datetime import datetime as _dt
            run.confirmed_at = _dt.utcnow()
            db.session.commit()
            print(f"💰 Đã chạy & xác nhận bảng lương T5/2026 — tổng {float(run.total_amount):,.0f}đ\n")
        else:
            print(f"⚠ Không chạy được bảng lương: {err}\n")

    # ────────────────────────────────────────────────────────────────────
    # TÓM TẮT
    # ────────────────────────────────────────────────────────────────────
    print("=" * 58)
    print("✅  SEED DEMO HOÀN THÀNH!")
    print("=" * 58)
    print()
    print("📌 Tài khoản đăng nhập  (mã tổ chức: grapecorp)")
    print("   ─────────────────────────────────────────────")
    print("   admin      / admin123      → Quản trị viên")
    print("   an.nv      / Employee@123  → HR Manager (Phòng IT)")
    print("   binh.tt    / Employee@123  → Lập trình viên")
    print("   cuong.lv   / Employee@123  → Lập trình viên")
    print("   dung.pt    / Employee@123  → Nhân viên kinh doanh")
    print("   em.hv      / Employee@123  → Nhân viên kinh doanh")
    print()
    print("📊 Dữ liệu đã tạo:")
    print("   • 2 phòng ban  |  3 chức vụ  |  3 cấu trúc lương  |  2 ca làm việc")
    print("   • 5 nhân viên + user account (đã gán ca làm việc)")
    print("   • 5 đơn nghỉ phép (2 Approved, 1 Rejected, 1 Pending)")
    print(f"  • {total_att} bản ghi chấm công (T5 + T6/2026)")
    print()
    print("💡 Gợi ý test:")
    print("   1. Dashboard → hôm nay ai đi làm / đi muộn / nghỉ + tổng công tháng")
    print("   2. Chấm công → tab Tổng công tháng → xuất CSV")
    print("   3. Bảng lương → Chạy lương tháng 5/2026 → xem phiếu lương")
    print("   4. Đăng nhập binh.tt → góc nhìn nhân viên (Chấm công GPS, Phiếu lương)")
    print("   5. Đăng nhập an.nv → duyệt đơn nghỉ của em.hv → tự sinh chấm công ON_LEAVE")
