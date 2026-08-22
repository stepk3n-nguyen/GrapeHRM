"""
Dịch vụ gửi Email thông báo (Background Threading).
Sử dụng smtplib để gửi email trực tiếp qua SMTP cấu hình trong .env.
Không dùng block request — sử dụng threading.Thread để chạy nền.
"""

import smtplib
import threading
from email.message import EmailMessage
from email.utils import formataddr


def _send_email_async(app, recipient, subject, body, is_html=False, tenant_id=None):
    """
    Hàm thực thi việc kết nối SMTP và gửi email.
    Chạy trong context của app (để lấy config) nhưng ở thread riêng.
    """
    with app.app_context():
        smtp_server = smtp_port = use_tls = username = password = sender = None

        # Ưu tiên SMTP riêng của tenant (nếu đã cấu hình)
        if tenant_id is not None:
            try:
                from app.models.tenant_config import TenantConfig
                from app.services.crypto_service import decrypt_secret
                tc = TenantConfig.query.filter_by(tenant_id=tenant_id).first()
                if tc and tc.mail_server:
                    smtp_server = tc.mail_server
                    smtp_port = tc.mail_port
                    use_tls = tc.mail_use_tls
                    username = tc.mail_username
                    password = decrypt_secret(tc.mail_password_encrypted)
                    sender = tc.mail_default_sender
            except Exception:
                smtp_server = None

        # Fallback: cấu hình hệ thống trong app.config
        if not smtp_server:
            smtp_server = app.config.get("MAIL_SERVER")
            smtp_port = app.config.get("MAIL_PORT")
            use_tls = app.config.get("MAIL_USE_TLS", True)
            username = app.config.get("MAIL_USERNAME")
            password = app.config.get("MAIL_PASSWORD")
            sender = app.config.get("MAIL_DEFAULT_SENDER")

        # Kiểm tra điều kiện cần
        if not all([smtp_server, smtp_port, username, password]):
            print(f"[EMAIL] Bỏ qua gửi email tới {recipient} vì chưa cấu hình SMTP.")
            print(f"[EMAIL MOCK] Tiêu đề: {subject}")
            return

        from app.models.email_log import EmailLog
        from app.extensions import db

        try:
            # Tạo gói tin email
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = formataddr(("GrapeHRM", sender)) if "<" not in sender else sender
            msg["To"] = recipient
            if is_html:
                msg.add_alternative(body, subtype='html')
            else:
                msg.set_content(body)

            # Kết nối SMTP
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            
            # StartTLS nếu cấu hình yêu cầu
            if use_tls:
                server.starttls()
            
            # Đăng nhập
            server.login(username, password)
            
            # Gửi và đóng kết nối
            server.send_message(msg)
            server.quit()
            
            print(f"[EMAIL] Gửi email thành công tới: {recipient}")
            
            # Log thành công
            log = EmailLog(tenant_id=tenant_id, recipient=recipient, subject=subject, status='SENT')
            db.session.add(log)
            db.session.commit()
            
        except Exception as e:
            # Chỉ log lỗi, không crash app chính vì chạy thread riêng
            print(f"[EMAIL ERROR] Gửi thất bại tới {recipient}. Lỗi: {str(e)}")
            
            # Log lỗi
            log = EmailLog(tenant_id=tenant_id, recipient=recipient, subject=subject, status='FAILED', error_message=str(e))
            db.session.add(log)
            try:
                db.session.commit()
            except Exception:
                pass

def send_email(app, recipient: str, subject: str, body: str, is_html: bool = False, tenant_id=None):
    """
    Hàm gọi từ ứng dụng (views/controllers).
    Khởi tạo một background thread để gửi email.
    
    Args:
        app: Flask app instance.
        recipient: Địa chỉ email người nhận.
        subject: Tiêu đề email.
        body: Nội dung email (plain text/html).
        is_html: Có phải là html không.
        tenant_id: Mã tenant (nếu có).
    """
    if not recipient:
        return

    # Thử lấy tenant_id từ g nếu đang trong request context
    if tenant_id is None:
        try:
            from flask import g
            if hasattr(g, 'tenant_id'):
                tenant_id = g.tenant_id
        except Exception:
            pass

    # Khởi tạo và chạy background thread
    thread = threading.Thread(
        target=_send_email_async,
        args=(app, recipient, subject, body, is_html, tenant_id),
        name=f"EmailThread-{recipient}"
    )
    thread.daemon = True  # Đảm bảo thread tự chết khi main process dừng
    thread.start()


# ── Templates mẫu cho module Leave ───────────────────────────────────────
from app.services.email_templates import (
    leave_submitted_html, leave_approved_html, 
    leave_rejected_html, leave_cancelled_html
)

def send_leave_request_submitted_email(app, hr_email, employee_name, leave_type_name, start_date, end_date):
    """Email gửi cho HR khi nhân viên nộp đơn."""
    subject = "[GrapeHRM] Đơn nghỉ phép mới cần phê duyệt"
    body = leave_submitted_html(employee_name, leave_type_name, start_date, end_date)
    send_email(app, hr_email, subject, body, is_html=True)


def send_leave_final_approved_email(app, employee_email, leave_type_name, start_date, end_date):
    """Email gửi cho Nhân viên khi đơn được duyệt hoàn tất (HR approve)."""
    subject = "[GrapeHRM] Đơn nghỉ phép được duyệt hoàn tất ✅"
    body = leave_approved_html(leave_type_name, start_date, end_date)
    send_email(app, employee_email, subject, body, is_html=True)


def send_leave_rejected_email(app, employee_email, leave_type_name, reason):
    """Email gửi cho Nhân viên khi đơn bị từ chối (bởi HR)."""
    subject = "[GrapeHRM] Đơn nghỉ phép bị từ chối ❌"
    body = leave_rejected_html(leave_type_name, reason)
    send_email(app, employee_email, subject, body, is_html=True)


def send_leave_cancelled_email(app, hr_email, employee_name, leave_type_name, start_date, end_date):
    """Email gửi cho HR khi nhân viên tự hủy đơn."""
    subject = "[GrapeHRM] Đơn nghỉ phép đã bị hủy ⚠️"
    body = leave_cancelled_html(employee_name, leave_type_name, start_date, end_date)
    send_email(app, hr_email, subject, body, is_html=True)


# ── Templates mẫu cho module Overtime ────────────────────────────────────
from app.services.email_templates import (
    overtime_submitted_html, overtime_approved_html,
    overtime_rejected_html, overtime_cancelled_html
)

def send_overtime_request_submitted_email(app, hr_email, employee_name, ot_type_label, date, hours):
    """Email gửi cho HR khi nhân viên đăng ký tăng ca."""
    subject = "[GrapeHRM] Đơn đăng ký tăng ca mới cần phê duyệt"
    body = overtime_submitted_html(employee_name, ot_type_label, date, hours)
    send_email(app, hr_email, subject, body, is_html=True)

def send_overtime_final_approved_email(app, employee_email, ot_type_label, date, hours):
    """Email gửi cho Nhân viên khi đơn tăng ca được duyệt."""
    subject = "[GrapeHRM] Đơn đăng ký tăng ca được duyệt ✅"
    body = overtime_approved_html(ot_type_label, date, hours)
    send_email(app, employee_email, subject, body, is_html=True)

def send_overtime_rejected_email(app, employee_email, ot_type_label, date, hours, reason=None):
    """Email gửi cho Nhân viên khi đơn tăng ca bị từ chối."""
    subject = "[GrapeHRM] Đơn đăng ký tăng ca bị từ chối ❌"
    body = overtime_rejected_html(ot_type_label, date, hours, reason)
    send_email(app, employee_email, subject, body, is_html=True)

def send_overtime_cancelled_email(app, hr_email, employee_name, ot_type_label, date, hours):
    """Email gửi cho HR khi nhân viên tự hủy đơn tăng ca."""
    subject = "[GrapeHRM] Đơn đăng ký tăng ca đã bị hủy ⚠️"
    body = overtime_cancelled_html(employee_name, ot_type_label, date, hours)
    send_email(app, hr_email, subject, body, is_html=True)
