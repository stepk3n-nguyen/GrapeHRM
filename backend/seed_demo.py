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
        LeaveRequest, LeaveApprovalLog, Attendance,
    )
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
                                 work_hours=7.75, status="LATE", source="MANUAL",
                                 note="Đến muộn")

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
    # 8. PHASE D — Hợp đồng + Tuyển dụng + Đánh giá hiệu suất
    # ────────────────────────────────────────────────────────────────────
    from app.models.contract import Contract
    from app.models.recruitment import JobPosting, Candidate
    from app.models.performance import ReviewCycle, PerformanceReview, ReviewScore

    # Hợp đồng cho từng nhân viên (Bình sắp hết hạn để demo cảnh báo)
    contract_specs = [
        dict(emp=emps["an.nv"],    type="INDEFINITE", start=date(2022, 1, 10), end=None,            num="HD-2022-001"),
        dict(emp=emps["binh.tt"],  type="FIXED_TERM", start=date(2025, 7, 1),  end=date(2026, 6, 30), num="HD-2025-014"),
        dict(emp=emps["cuong.lv"], type="FIXED_TERM", start=date(2024, 8, 15), end=date(2026, 8, 14), num="HD-2024-009"),
        dict(emp=emps["dung.pt"],  type="PROBATION",  start=date(2026, 5, 1),  end=date(2026, 7, 31), num="HD-2026-021"),
        dict(emp=emps["em.hv"],    type="FIXED_TERM", start=date(2025, 2, 1),  end=date(2027, 1, 31), num="HD-2025-005"),
    ]
    c_count = 0
    for cs in contract_specs:
        if not Contract.query.filter_by(tenant_id=TID, employee_id=cs["emp"].id).first():
            db.session.add(Contract(
                tenant_id=TID, employee_id=cs["emp"].id, contract_number=cs["num"],
                contract_type=cs["type"], start_date=cs["start"], end_date=cs["end"],
                signed_date=cs["start"], status="ACTIVE",
            ))
            c_count += 1
    db.session.commit()
    if c_count:
        print(f"  ✓ {c_count} hợp đồng lao động (Bình sắp hết hạn 30/06)")

    # Tin tuyển dụng + ứng viên
    job = JobPosting.query.filter_by(tenant_id=TID, title="Lập trình viên Backend").first()
    if not job:
        job = JobPosting(tenant_id=TID, title="Lập trình viên Backend",
                         department_id=dept_it.id, quantity=2,
                         description="Tuyển 2 BE (Python/Flask), 1-3 năm kinh nghiệm.",
                         status="OPEN", posted_date=date(2026, 6, 1))
        db.session.add(job)
        db.session.flush()
        for name, email, stage in [
            ("Vũ Minh Khôi", "khoi.vm@gmail.com", "INTERVIEW"),
            ("Đỗ Thu Hà", "ha.dt@gmail.com", "APPLIED"),
            ("Bùi Tiến Dũng", "dung.bt@gmail.com", "OFFERED"),
        ]:
            db.session.add(Candidate(tenant_id=TID, job_posting_id=job.id, full_name=name,
                                     email=email, stage=stage, applied_date=date(2026, 6, 5)))
        db.session.commit()
        print("  ✓ 1 tin tuyển dụng + 3 ứng viên")

    # Kỳ đánh giá + phiếu đánh giá (Bình, Cường)
    cycle = ReviewCycle.query.filter_by(tenant_id=TID, name="Đánh giá Quý 2/2026").first()
    if not cycle:
        cycle = ReviewCycle(tenant_id=TID, name="Đánh giá Quý 2/2026",
                            start_date=date(2026, 4, 1), end_date=date(2026, 6, 30), status="OPEN")
        db.session.add(cycle)
        db.session.flush()
        review_specs = [
            dict(emp=emps["binh.tt"], scores=[("Chất lượng công việc", 9, 2), ("Tiến độ", 8, 1), ("Thái độ", 9, 1)], cmt="Hoàn thành tốt, chủ động."),
            dict(emp=emps["cuong.lv"], scores=[("Chất lượng công việc", 7, 2), ("Tiến độ", 8, 1), ("Thái độ", 8, 1)], cmt="Ổn định, cần cải thiện chất lượng."),
        ]
        for rs in review_specs:
            r = PerformanceReview(tenant_id=TID, cycle_id=cycle.id, employee_id=rs["emp"].id,
                                  reviewer_id=admin_user.id if admin_user else None,
                                  status="SUBMITTED", comments=rs["cmt"])
            db.session.add(r)
            db.session.flush()
            tw = sum(w for _, _, w in rs["scores"])
            tot = 0
            for crit, sc, w in rs["scores"]:
                db.session.add(ReviewScore(review_id=r.id, criterion=crit, score=sc, weight=w))
                tot += sc * w
            r.overall_score = round(tot / tw, 1)
        db.session.commit()
        print("  ✓ 1 kỳ đánh giá + 2 phiếu đánh giá hiệu suất\n")

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
    print("   • 2 phòng ban  |  3 chức vụ  |  3 cấu trúc lương")
    print("   • 5 nhân viên + user account")
    print("   • 5 đơn nghỉ phép (2 Approved, 1 Rejected, 1 Pending)")
    print(f"  • {total_att} bản ghi chấm công (T5 + T6/2026)")
    print()
    print("💡 Gợi ý test:")
    print("   1. Dashboard → xem tổng quan nhân sự + biểu đồ")
    print("   2. Bảng lương → Chạy lương tháng 5/2026 → xem phiếu lương")
    print("   3. Báo cáo → Chấm công & Nghỉ phép")
    print("   4. Đăng nhập binh.tt → góc nhìn nhân viên (Chấm công GPS, Phiếu lương)")
    print("   5. Đăng nhập an.nv → duyệt đơn nghỉ của em.hv")
