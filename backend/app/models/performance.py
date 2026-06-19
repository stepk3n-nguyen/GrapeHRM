"""
Models Đánh giá hiệu suất — kỳ đánh giá, phiếu đánh giá nhân viên, điểm theo tiêu chí.
"""

from app.extensions import db
from app.models.base import TenantMixin, TimestampMixin


class ReviewCycle(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "review_cycles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)       # vd "Đánh giá Quý 2/2026"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.Enum("OPEN", "CLOSED", name="review_cycle_status"), default="OPEN")

    reviews = db.relationship("PerformanceReview", backref="cycle", cascade="all, delete-orphan")


class PerformanceReview(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = "performance_reviews"

    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey("review_cycles.id", ondelete="CASCADE"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    overall_score = db.Column(db.Numeric(4, 1), nullable=True)   # 0–10
    status = db.Column(db.Enum("PENDING", "SUBMITTED", name="review_status"), default="PENDING")
    comments = db.Column(db.Text)

    __table_args__ = (db.UniqueConstraint("cycle_id", "employee_id", name="uq_cycle_employee"),)

    employee = db.relationship("Employee")
    scores = db.relationship("ReviewScore", backref="review", cascade="all, delete-orphan")


class ReviewScore(db.Model):
    __tablename__ = "review_scores"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("performance_reviews.id", ondelete="CASCADE"), nullable=False)
    criterion = db.Column(db.String(120), nullable=False)   # vd "Chất lượng công việc"
    score = db.Column(db.Numeric(4, 1), nullable=False)     # 0–10
    weight = db.Column(db.Integer, default=1)
