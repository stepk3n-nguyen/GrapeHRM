"""
Xuất phiếu lương ra PDF bằng reportlab.

Dùng font DejaVu Sans (bundle sẵn trong app/assets/fonts) để hiển thị
tiếng Việt đầy đủ dấu — font mặc định Helvetica của reportlab không có
glyph tiếng Việt nên sẽ vỡ chữ.
"""

import io
import os

_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_FONTS_REGISTERED = False


def _register_fonts():
    """Đăng ký font Unicode (chạy 1 lần). Fallback Helvetica nếu thiếu file."""
    global _FONT, _FONT_BOLD, _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    _FONTS_REGISTERED = True
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
        regular = os.path.join(fonts_dir, "DejaVuSans.ttf")
        bold = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("VNSans", regular))
            pdfmetrics.registerFont(TTFont("VNSans-Bold", bold))
            _FONT, _FONT_BOLD = "VNSans", "VNSans-Bold"
    except Exception:
        pass  # giữ Helvetica — PDF vẫn xuất được dù chữ có dấu bị vỡ


def _money(v):
    return f"{float(v):,.0f}".replace(",", ".") + " đ"


def build_payslip_pdf(payslip, employee, run):
    """Trả về bytes PDF cho 1 phiếu lương."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    _register_fonts()

    # Tên công ty in trên phiếu lương
    from app.models.tenant import Tenant
    tenant = Tenant.query.get(run.tenant_id)
    company_name = tenant.name if tenant else "GrapeHRM"
    company_addr = (tenant.address or "") if tenant else ""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    company_style = ParagraphStyle("c", parent=styles["Normal"], fontName=_FONT_BOLD,
                                   fontSize=13, textColor=colors.HexColor("#1F3864"))
    company_sub = ParagraphStyle("cs", parent=styles["Normal"], fontName=_FONT,
                                 fontSize=8.5, textColor=colors.HexColor("#6C757D"))
    title = ParagraphStyle("t", parent=styles["Title"], fontName=_FONT_BOLD, fontSize=16,
                           spaceBefore=6, spaceAfter=2)
    h = ParagraphStyle("h", parent=styles["Normal"], fontName=_FONT, fontSize=10,
                       alignment=1, textColor=colors.HexColor("#6C757D"))

    elems = [
        Paragraph(company_name, company_style),
    ]
    if company_addr:
        elems.append(Paragraph(company_addr, company_sub))
    elems += [
        Spacer(1, 2 * mm),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E5B9F")),
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
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6C757D")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#6C757D")),
        ("FONTNAME", (1, 0), (1, 0), _FONT_BOLD),
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
            rows.append([f"(−) {it.name}", "−" + _money(it.amount)])
    rows.append(["THỰC NHẬN", _money(payslip.net_salary)])

    t = Table(rows, colWidths=[110 * mm, 50 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E5B9F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CED4DA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7F9FC")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F0FE")),
        ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elems.append(t)

    footer = ParagraphStyle("f", parent=styles["Normal"], fontName=_FONT, fontSize=8,
                            textColor=colors.HexColor("#9AA0A6"))
    elems += [
        Spacer(1, 8 * mm),
        Paragraph("Phiếu lương được tạo tự động từ dữ liệu chấm công GrapeHRM — vui lòng liên hệ HR nếu có sai lệch.", footer),
    ]

    doc.build(elems)
    buf.seek(0)
    return buf.read()
