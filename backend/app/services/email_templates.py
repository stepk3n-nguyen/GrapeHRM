"""
Email HTML templates.
Cung cấp các hàm trả về chuỗi HTML chuẩn cho các luồng thông báo.
Sử dụng inline CSS để tương thích tốt nhất với Gmail, Outlook, Apple Mail.
"""

# Base layout (wrapper)
def _base_template(content: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GrapeHRM Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f5f5f5; color: #333333; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-top: 20px; margin-bottom: 20px;">
        
        <!-- Header -->
        <div style="background-color: #0A6ED1; padding: 24px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 0.5px;">GrapeHRM</h1>
        </div>
        
        <!-- Body -->
        <div style="padding: 32px 24px;">
            {content}
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #eeeeee;">
            <p style="margin: 0; color: #888888; font-size: 12px;">
                Đây là email tự động từ hệ thống GrapeHRM.<br>
                Vui lòng không trả lời email này.
            </p>
        </div>
        
    </div>
</body>
</html>
    """

def leave_submitted_html(employee_name: str, leave_type_name: str, start_date, end_date) -> str:
    content = f"""
        <h2 style="margin-top: 0; color: #222222; font-size: 20px;">Đơn nghỉ phép mới cần duyệt</h2>
        <p>Xin chào HR,</p>
        <p>Hệ thống vừa ghi nhận một đơn xin nghỉ phép mới chờ phê duyệt:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; background-color: #f9fbfd; border-radius: 6px; border: 1px solid #e1e8ed;">
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666; width: 40%;"><strong>Nhân viên:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;"><strong>{employee_name}</strong></td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666;"><strong>Loại phép:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{leave_type_name}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666;"><strong>Từ ngày:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{start_date}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; color: #666666;"><strong>Đến ngày:</strong></td>
                <td style="padding: 12px 16px; color: #111111;">{end_date}</td>
            </tr>
        </table>
        
        <p style="margin-bottom: 30px;">Vui lòng đăng nhập vào hệ thống để xem chi tiết và phê duyệt đơn này.</p>
        
        <div style="text-align: center;">
            <a href="http://localhost:3000/leave" style="display: inline-block; padding: 12px 24px; background-color: #0A6ED1; color: #ffffff; text-decoration: none; border-radius: 4px; font-weight: 600; text-align: center;">Vào hệ thống</a>
        </div>
    """
    return _base_template(content)

def leave_approved_html(leave_type_name: str, start_date, end_date) -> str:
    content = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: inline-block; width: 48px; height: 48px; background-color: #e6f4ea; border-radius: 50%; line-height: 48px; color: #1e8e3e; font-size: 24px; font-weight: bold;">✓</div>
        </div>
        <h2 style="margin-top: 0; color: #222222; font-size: 20px; text-align: center;">Đơn xin nghỉ phép đã được duyệt</h2>
        <p>Xin chào,</p>
        <p>Đơn xin nghỉ phép của bạn đã được HR <strong>phê duyệt</strong>.</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; background-color: #f9fbfd; border-radius: 6px; border: 1px solid #e1e8ed;">
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666; width: 40%;"><strong>Loại phép:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{leave_type_name}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666;"><strong>Từ ngày:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{start_date}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; color: #666666;"><strong>Đến ngày:</strong></td>
                <td style="padding: 12px 16px; color: #111111;">{end_date}</td>
            </tr>
        </table>
        
        <p>Chúc bạn có thời gian nghỉ ngơi vui vẻ!</p>
    """
    return _base_template(content)

def leave_rejected_html(leave_type_name: str, reason: str) -> str:
    content = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: inline-block; width: 48px; height: 48px; background-color: #fce8e6; border-radius: 50%; line-height: 48px; color: #d93025; font-size: 24px; font-weight: bold;">✕</div>
        </div>
        <h2 style="margin-top: 0; color: #222222; font-size: 20px; text-align: center;">Đơn xin nghỉ phép bị từ chối</h2>
        <p>Xin chào,</p>
        <p>Rất tiếc, đơn xin nghỉ phép (<strong>{leave_type_name}</strong>) của bạn đã bị <strong>từ chối</strong>.</p>
        
        <div style="background-color: #fef7f6; border-left: 4px solid #d93025; padding: 16px; margin: 24px 0;">
            <p style="margin: 0; color: #c5221f;"><strong>Lý do từ chối:</strong></p>
            <p style="margin: 8px 0 0 0; color: #333333;">{reason or 'Không có ghi chú'}</p>
        </div>
        
        <p>Vui lòng liên hệ trực tiếp với bộ phận HR để biết thêm chi tiết hoặc nộp lại đơn khác với thời gian phù hợp hơn.</p>
    """
    return _base_template(content)

def leave_cancelled_html(employee_name: str, leave_type_name: str, start_date, end_date) -> str:
    content = f"""
        <h2 style="margin-top: 0; color: #222222; font-size: 20px;">Đơn xin nghỉ phép đã bị hủy</h2>
        <p>Xin chào HR,</p>
        <p>Nhân viên <strong>{employee_name}</strong> vừa <strong>hủy bỏ</strong> đơn xin nghỉ phép đang chờ duyệt:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; background-color: #fcfcfc; border-radius: 6px; border: 1px solid #eeeeee;">
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #888888; width: 40%;"><strong>Loại phép:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #555555; text-decoration: line-through;">{leave_type_name}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #888888;"><strong>Từ ngày:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #555555; text-decoration: line-through;">{start_date}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; color: #888888;"><strong>Đến ngày:</strong></td>
                <td style="padding: 12px 16px; color: #555555; text-decoration: line-through;">{end_date}</td>
            </tr>
        </table>
        
        <p>Hệ thống đã cập nhật trạng thái đơn thành "Đã hủy". Bạn không cần thực hiện thêm thao tác nào cho đơn này.</p>
    """
    return _base_template(content)

def attendance_checked_in_html(employee_name: str, check_in_time: str) -> str:
    content = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: inline-block; width: 48px; height: 48px; background-color: #e6f4ea; border-radius: 50%; line-height: 48px; color: #1e8e3e; font-size: 24px; font-weight: bold;">✓</div>
        </div>
        <h2 style="margin-top: 0; color: #222222; font-size: 20px; text-align: center;">Chấm công thành công</h2>
        <p>Xin chào <strong>{employee_name}</strong>,</p>
        <p>Hệ thống đã ghi nhận yêu cầu chấm công (Check-in) của bạn với thông tin như sau:</p>
        
        <div style="background-color: #f9fbfd; border: 1px solid #e1e8ed; border-radius: 6px; padding: 16px; margin: 24px 0; text-align: center;">
            <p style="margin: 0; color: #666666; font-size: 14px;">Thời gian ghi nhận</p>
            <p style="margin: 8px 0 0 0; color: #0A6ED1; font-size: 28px; font-weight: bold;">{check_in_time}</p>
        </div>
        
        <p>Chúc bạn một ngày làm việc hiệu quả và tràn đầy năng lượng!</p>
    """
    return _base_template(content)

def overtime_submitted_html(employee_name: str, ot_type_label: str, date: str, hours: float) -> str:
    content = f"""
        <h2 style="margin-top: 0; color: #222222; font-size: 20px;">Đơn đăng ký tăng ca mới cần duyệt</h2>
        <p>Xin chào HR,</p>
        <p>Hệ thống vừa ghi nhận một đơn đăng ký tăng ca mới chờ phê duyệt:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; background-color: #f9fbfd; border-radius: 6px; border: 1px solid #e1e8ed;">
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666; width: 40%;"><strong>Nhân viên:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;"><strong>{employee_name}</strong></td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666;"><strong>Loại tăng ca:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{ot_type_label}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666;"><strong>Ngày:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{date}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; color: #666666;"><strong>Số giờ:</strong></td>
                <td style="padding: 12px 16px; color: #111111;">{hours} giờ</td>
            </tr>
        </table>
        
        <p style="margin-bottom: 30px;">Vui lòng đăng nhập vào hệ thống để xem chi tiết và phê duyệt đơn này.</p>
        
        <div style="text-align: center;">
            <a href="http://localhost:3000/compensation" style="display: inline-block; padding: 12px 24px; background-color: #0A6ED1; color: #ffffff; text-decoration: none; border-radius: 4px; font-weight: 600; text-align: center;">Vào hệ thống</a>
        </div>
    """
    return _base_template(content)

def overtime_approved_html(ot_type_label: str, date: str, hours: float) -> str:
    content = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: inline-block; width: 48px; height: 48px; background-color: #e6f4ea; border-radius: 50%; line-height: 48px; color: #1e8e3e; font-size: 24px; font-weight: bold;">✓</div>
        </div>
        <h2 style="margin-top: 0; color: #222222; font-size: 20px; text-align: center;">Đơn đăng ký tăng ca đã được duyệt</h2>
        <p>Xin chào,</p>
        <p>Đơn đăng ký tăng ca của bạn đã được <strong>phê duyệt</strong>.</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; background-color: #f9fbfd; border-radius: 6px; border: 1px solid #e1e8ed;">
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666; width: 40%;"><strong>Loại tăng ca:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{ot_type_label}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666;"><strong>Ngày:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{date}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; color: #666666;"><strong>Số giờ:</strong></td>
                <td style="padding: 12px 16px; color: #111111;">{hours} giờ</td>
            </tr>
        </table>
        
        <p>Cảm ơn sự đóng góp của bạn!</p>
    """
    return _base_template(content)

def overtime_rejected_html(ot_type_label: str, date: str, hours: float, reason: str = None) -> str:
    content = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: inline-block; width: 48px; height: 48px; background-color: #fce8e6; border-radius: 50%; line-height: 48px; color: #d93025; font-size: 24px; font-weight: bold;">✕</div>
        </div>
        <h2 style="margin-top: 0; color: #222222; font-size: 20px; text-align: center;">Đơn đăng ký tăng ca bị từ chối</h2>
        <p>Xin chào,</p>
        <p>Rất tiếc, đơn đăng ký tăng ca của bạn vào ngày <strong>{date}</strong> đã bị <strong>từ chối</strong>.</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; background-color: #f9fbfd; border-radius: 6px; border: 1px solid #e1e8ed;">
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #666666; width: 40%;"><strong>Loại tăng ca:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e1e8ed; color: #111111;">{ot_type_label}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; color: #666666;"><strong>Số giờ:</strong></td>
                <td style="padding: 12px 16px; color: #111111;">{hours} giờ</td>
            </tr>
        </table>
"""
    if reason:
        content += f"""
        <div style="background-color: #fef7f6; border-left: 4px solid #d93025; padding: 16px; margin: 24px 0;">
            <p style="margin: 0; color: #c5221f;"><strong>Lý do từ chối:</strong></p>
            <p style="margin: 8px 0 0 0; color: #333333;">{reason}</p>
        </div>
"""
    content += """
        <p>Vui lòng liên hệ trực tiếp với quản lý hoặc bộ phận HR để biết thêm chi tiết.</p>
    """
    return _base_template(content)

def overtime_cancelled_html(employee_name: str, ot_type_label: str, date: str, hours: float) -> str:
    content = f"""
        <h2 style="margin-top: 0; color: #222222; font-size: 20px;">Đơn đăng ký tăng ca đã bị hủy</h2>
        <p>Xin chào HR,</p>
        <p>Nhân viên <strong>{employee_name}</strong> vừa <strong>hủy bỏ</strong> đơn đăng ký tăng ca đang chờ duyệt:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 24px 0; background-color: #fcfcfc; border-radius: 6px; border: 1px solid #eeeeee;">
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #888888; width: 40%;"><strong>Loại tăng ca:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #555555; text-decoration: line-through;">{ot_type_label}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #888888;"><strong>Ngày:</strong></td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eeeeee; color: #555555; text-decoration: line-through;">{date}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; color: #888888;"><strong>Số giờ:</strong></td>
                <td style="padding: 12px 16px; color: #555555; text-decoration: line-through;">{hours} giờ</td>
            </tr>
        </table>
        
        <p>Hệ thống đã cập nhật trạng thái đơn thành "Đã hủy". Bạn không cần thực hiện thêm thao tác nào cho đơn này.</p>
    """
    return _base_template(content)
