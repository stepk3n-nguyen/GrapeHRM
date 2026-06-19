"""
Xuất phiếu lương ra PDF bằng reportlab.
"""

import io


def _money(v):
    return f"{float(v):,.0f}".replace(",", ".") + " đ"


def build_payslip_pdf(payslip, employee, run):
    """Trả về bytes PDF cho 1 phiếu lương."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=styles["Title"], fontSize=16)
    h = ParagraphStyle("h", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#6C757D"))

    elems = [
        Paragraph("PHIẾU LƯƠNG", title),
        Paragraph(f"Kỳ lương: tháng {run.month}/{run.year}", h),
        Spacer(1, 6 * mm),
    ]

    info = [
        ["Nhân viên:", employee.full_name(), "Mã NV:", employee.employee_id or "—"],
        ["Ngày công:", f"{float(payslip.total_work_days):g}/{payslip.standard_work_days}",
         "Ngày nghỉ có lương:", f"{float(payslip.total_leave_days):g}"],
        ["Tăng ca:", f"{float(payslip.overtime_hours or 0):g} giờ",
         "Người phụ thuộc:", f"{payslip.num_dependents or 0}"],
        ["Tổng thu nhập:", _money(payslip.gross_salary or 0),
         "TN tính thuế:", _money(payslip.taxable_income or 0)],
    ]
    t_info = Table(info, colWidths=[35 * mm, 55 * mm, 40 * mm, 40 * mm])
    t_info.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6C757D")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#6C757D")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems += [t_info, Spacer(1, 5 * mm)]

    std = payslip.standard_work_days or 1
    paid_days = float(payslip.total_work_days) + float(payslip.total_leave_days)
    prorated_basic = float(payslip.basic_salary) * min(paid_days / std, 1.0)

    rows = [["Khoản mục", "Số tiền"]]
    rows.append(["Lương cơ bản (theo ngày công)", _money(prorated_basic)])
    for it in payslip.items:
        if it.item_type == "ALLOWANCE":
            rows.append([f"(+) {it.name}", _money(it.amount)])
    for it in payslip.items:
        if it.item_type == "DEDUCTION":
            rows.append([f"(−) {it.name}", "-" + _money(it.amount)])
    rows.append(["THỰC NHẬN", _money(payslip.net_salary)])

    t = Table(rows, colWidths=[110 * mm, 50 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A6ED1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CED4DA")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F0FE")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elems.append(t)

    doc.build(elems)
    buf.seek(0)
    return buf.read()
