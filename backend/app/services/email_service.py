"""
Dịch vụ gửi Email thông báo (Background Threading).
Sử dụng smtplib để gửi email trực tiếp qua SMTP cấu hình trong .env.
Không dùng block request — sử dụng threading.Thread để chạy nền.
"""

import smtplib
import threading
from email.message import EmailMessage
from email.utils import formataddr


def _send_email_async(app, recipient, subject, body):
    """
    Hàm thực thi việc kết nối SMTP và gửi email.
    Chạy trong context của app (để lấy config) nhưng ở thread riêng.
    """
    with app.app_context():
        # Đọc cấu hình từ app.config
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

        try:
            # Tạo gói tin email
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = formataddr(("GrapeHRM", sender)) if "<" not in sender else sender
            msg["To"] = recipient
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
            
        except Exception as e:
            # Chỉ log lỗi, không crash app chính vì chạy thread riêng
            print(f"[EMAIL ERROR] Gửi thất bại tới {recipient}. Lỗi: {str(e)}")


def send_email(app, recipient: str, subject: str, body: str):
    """
    Hàm gọi từ ứng dụng (views/controllers).
    Khởi tạo một background thread để gửi email.
    
    Args:
        app: Flask app instance.
        recipient: Địa chỉ email người nhận.
        subject: Tiêu đề email.
        body: Nội dung email (plain text).
    """
    if not recipient:
        return

    # Khởi tạo và chạy background thread
    thread = threading.Thread(
        target=_send_email_async,
        args=(app, recipient, subject, body),
        name=f"EmailThread-{recipient}"
    )
    thread.daemon = True  # Đảm bảo thread tự chết khi main process dừng
    thread.start()


# ── Templates mẫu cho module Leave ───────────────────────────────────────

def send_leave_request_submitted_email(app, hr_email, employee_name, leave_type_name, start_date, end_date):
    """Email gửi cho HR khi nhân viên nộp đơn."""
    subject = "[GrapeHRM] Đơn nghỉ phép mới cần phê duyệt"
    body = (
        f"Xin chào HR,\n\n"
        f"Nhân viên {employee_name} vừa nộp đơn xin nghỉ phép ({leave_type_name}) "
        f"từ ngày {start_date} đến {end_date}.\n\n"
        f"Vui lòng đăng nhập GrapeHRM để xem chi tiết và phê duyệt.\n\n"
        f"Trân trọng,\nGrapeHRM System"
    )
    send_email(app, hr_email, subject, body)


def send_leave_final_approved_email(app, employee_email, leave_type_name, start_date, end_date):
    """Email gửi cho Nhân viên khi đơn được duyệt hoàn tất (HR approve)."""
    subject = "[GrapeHRM] Đơn nghỉ phép được duyệt hoàn tất ✅"
    body = (
        f"Xin chào,\n\n"
        f"Đơn xin nghỉ phép ({leave_type_name}) của bạn "
        f"từ ngày {start_date} đến {end_date} đã được phê duyệt thành công.\n\n"
        f"Chúc bạn có thời gian nghỉ ngơi vui vẻ!\n\n"
        f"Trân trọng,\nGrapeHRM System"
    )
    send_email(app, employee_email, subject, body)


def send_leave_rejected_email(app, employee_email, leave_type_name, reason):
    """Email gửi cho Nhân viên khi đơn bị từ chối (bởi HR)."""
    subject = "[GrapeHRM] Đơn nghỉ phép bị từ chối ❌"
    body = (
        f"Xin chào,\n\n"
        f"Rất tiếc, đơn xin nghỉ phép ({leave_type_name}) của bạn đã bị từ chối.\n"
        f"Lý do: {reason or 'Không có ghi chú'}\n\n"
        f"Vui lòng liên hệ HR để biết thêm chi tiết.\n\n"
        f"Trân trọng,\nGrapeHRM System"
    )
    send_email(app, employee_email, subject, body)
