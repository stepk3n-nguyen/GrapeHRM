"""
Models Tuyển dụng — tin tuyển dụng và ứng viên.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class JobPosting(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "job_postings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    status = db.Column(db.Enum("OPEN", "CLOSED", name="job_posting_status"), default="OPEN")
    posted_date = db.Column(db.Date)

    department = db.relationship("Department")
    candidates = db.relationship("Candidate", backref="job_posting", cascade="all, delete-orphan")


class Candidate(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    job_posting_id = db.Column(db.Integer, db.ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    cv_url = db.Column(db.Text)

    # Luồng tuyển: Nộp hồ sơ → Phỏng vấn → Mời nhận việc → Trúng tuyển / Loại
    stage = db.Column(
        db.Enum("APPLIED", "INTERVIEW", "OFFERED", "HIRED", "REJECTED", name="candidate_stage"),
        default="APPLIED",
    )
    note = db.Column(db.Text)
    applied_date = db.Column(db.Date)

    # Khi chuyển thành nhân viên, lưu lại liên kết để không tạo trùng
    hired_employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
