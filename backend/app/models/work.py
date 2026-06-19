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

    # Toạ độ tâm điểm (vĩ độ / kinh độ)
    latitude = db.Column(db.Numeric(9, 6), nullable=False)
    longitude = db.Column(db.Numeric(9, 6), nullable=False)

    # Bán kính cho phép chấm công (mét)
    radius_meters = db.Column(db.Integer, nullable=False, default=200)

    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<WorkLocation {self.name} r={self.radius_meters}m>"


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
