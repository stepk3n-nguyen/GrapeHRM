"""
Model cấu hình chấm công:
- WorkLocation: địa điểm làm việc (toạ độ + bán kính) để kiểm tra geofence.
- WorkShift: ca làm việc (giờ vào/ra) để tự suy ra đi muộn và giờ công chuẩn.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class WorkLocation(TenantMixin, TimestampMixin, db.Model):
    """Địa điểm làm việc — dùng để xác định nhân viên có chấm công trong
    phạm vi công ty hay không (geofence)."""

    __tablename__ = "work_locations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)

    is_active = db.Column(db.Boolean, default=True)

    # Danh sách IP Public cho phép chấm công (phân cách bằng dấu phẩy)
    # Ví dụ: "113.23.45.67,113.23.45.68"
    # Nếu để trống → chỉ dùng GPS geofence
    allowed_ips = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<WorkLocation {self.name}>"


class WorkShift(TenantMixin, TimestampMixin, db.Model):
    """Ca làm việc — định nghĩa giờ vào/ra chuẩn để hệ thống tự tính
    trạng thái đi muộn và thời lượng làm việc."""

    __tablename__ = "work_shifts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Số phút trễ tối đa vẫn coi là đúng giờ (qua mốc này = LATE)
    late_threshold_minutes = db.Column(db.Integer, default=15)

    # Số phút nghỉ giữa ca (trừ khỏi giờ công)
    break_minutes = db.Column(db.Integer, default=60)

    is_default = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<WorkShift {self.name} {self.start_time}-{self.end_time}>"
