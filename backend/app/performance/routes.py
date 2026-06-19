"""
Blueprint Đánh giá hiệu suất: kỳ đánh giá + phiếu đánh giá nhân viên (điểm theo tiêu chí).
HR/Admin quản lý; nhân viên xem được phiếu đánh giá của chính mình.
"""

from datetime import datetime, date

from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.extensions import db
from app.models.performance import ReviewCycle, PerformanceReview, ReviewScore
from app.models.employee import Employee
from app.models.user import User
from . import performance_bp


def _is_hr():
    return get_jwt().get("role") in ("super_admin", "admin", "hr_manager")


def _guard():
    if not _is_hr():
        return jsonify({"error": "Không có quyền truy cập"}), 403
    return None


def _parse(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").date() if d else None
    except (ValueError, TypeError):
        return None


# ── KỲ ĐÁNH GIÁ ─────────────────────────────────────────────────────────
def _serialize_cycle(c):
    return {
        "id": c.id, "name": c.name,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "status": c.status, "review_count": len(c.reviews),
    }


@performance_bp.route("/review-cycles", methods=["GET"])
@jwt_required()
def list_cycles():
    block = _guard()
    if block:
        return block
    items = ReviewCycle.query.filter_by(tenant_id=g.tenant_id).order_by(ReviewCycle.id.desc()).all()
    return jsonify([_serialize_cycle(c) for c in items]), 200


@performance_bp.route("/review-cycles", methods=["POST"])
@jwt_required()
def create_cycle():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    if not (d.get("name") or "").strip():
        return jsonify({"error": "Thiếu tên kỳ đánh giá"}), 400
    c = ReviewCycle(
        tenant_id=g.tenant_id, name=d["name"].strip(),
        start_date=_parse(d.get("start_date")), end_date=_parse(d.get("end_date")),
        status=d.get("status", "OPEN"),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Đã tạo kỳ đánh giá", "id": c.id}), 201


@performance_bp.route("/review-cycles/<int:cyid>", methods=["PUT"])
@jwt_required()
def update_cycle(cyid):
    block = _guard()
    if block:
        return block
    c = ReviewCycle.query.filter_by(id=cyid, tenant_id=g.tenant_id).first()
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    d = request.get_json(silent=True) or {}
    if "name" in d:
        c.name = d["name"].strip() or c.name
    if "status" in d:
        c.status = d["status"]
    for f in ("start_date", "end_date"):
        if f in d:
            setattr(c, f, _parse(d[f]))
    db.session.commit()
    return jsonify({"message": "Đã cập nhật"}), 200


@performance_bp.route("/review-cycles/<int:cyid>", methods=["DELETE"])
@jwt_required()
def delete_cycle(cyid):
    block = _guard()
    if block:
        return block
    c = ReviewCycle.query.filter_by(id=cyid, tenant_id=g.tenant_id).first()
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


# ── PHIẾU ĐÁNH GIÁ ──────────────────────────────────────────────────────
def _serialize_review(r, detail=False):
    base = {
        "id": r.id, "cycle_id": r.cycle_id, "cycle_name": r.cycle.name if r.cycle else None,
        "employee_id": r.employee_id,
        "employee_name": r.employee.full_name() if r.employee else "?",
        "employee_code": r.employee.employee_id if r.employee else None,
        "overall_score": float(r.overall_score) if r.overall_score is not None else None,
        "status": r.status, "comments": r.comments,
    }
    if detail:
        base["scores"] = [{"id": s.id, "criterion": s.criterion, "score": float(s.score), "weight": s.weight} for s in r.scores]
    return base


@performance_bp.route("/performance-reviews", methods=["GET"])
@jwt_required()
def list_reviews():
    q = PerformanceReview.query.filter_by(tenant_id=g.tenant_id)
    if not _is_hr():
        # Nhân viên chỉ xem phiếu đánh giá của chính mình
        user = User.query.get(int(get_jwt_identity()))
        if not user or not user.employee_id:
            return jsonify([]), 200
        q = q.filter_by(employee_id=user.employee_id, status="SUBMITTED")
    if request.args.get("cycle_id"):
        q = q.filter_by(cycle_id=request.args.get("cycle_id", type=int))
    items = q.order_by(PerformanceReview.id.desc()).all()
    return jsonify([_serialize_review(r, detail=True) for r in items]), 200


def _recalc_overall(review):
    if not review.scores:
        review.overall_score = None
        return
    tw = sum(s.weight or 1 for s in review.scores)
    review.overall_score = round(sum(float(s.score) * (s.weight or 1) for s in review.scores) / tw, 1) if tw else None


@performance_bp.route("/performance-reviews", methods=["POST"])
@jwt_required()
def create_review():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    cycle_id, emp_id = d.get("cycle_id"), d.get("employee_id")
    if not cycle_id or not emp_id:
        return jsonify({"error": "Thiếu kỳ đánh giá hoặc nhân viên"}), 400
    if not ReviewCycle.query.filter_by(id=cycle_id, tenant_id=g.tenant_id).first():
        return jsonify({"error": "Kỳ đánh giá không hợp lệ"}), 400
    if not Employee.query.filter_by(id=emp_id, tenant_id=g.tenant_id).first():
        return jsonify({"error": "Nhân viên không hợp lệ"}), 400
    if PerformanceReview.query.filter_by(cycle_id=cycle_id, employee_id=emp_id).first():
        return jsonify({"error": "Nhân viên đã có phiếu trong kỳ này"}), 409

    r = PerformanceReview(
        tenant_id=g.tenant_id, cycle_id=cycle_id, employee_id=emp_id,
        reviewer_id=int(get_jwt_identity()), status="PENDING", comments=d.get("comments"),
    )
    db.session.add(r)
    db.session.flush()
    for s in (d.get("scores") or []):
        if s.get("criterion"):
            db.session.add(ReviewScore(review_id=r.id, criterion=s["criterion"],
                                       score=float(s.get("score") or 0), weight=int(s.get("weight") or 1)))
    _recalc_overall(r)
    db.session.commit()
    return jsonify({"message": "Đã tạo phiếu đánh giá", "id": r.id}), 201


@performance_bp.route("/performance-reviews/<int:rid>", methods=["PUT"])
@jwt_required()
def update_review(rid):
    block = _guard()
    if block:
        return block
    r = PerformanceReview.query.filter_by(id=rid, tenant_id=g.tenant_id).first()
    if not r:
        return jsonify({"error": "Không tìm thấy"}), 404
    d = request.get_json(silent=True) or {}
    if "comments" in d:
        r.comments = d["comments"]
    if "status" in d and d["status"] in ("PENDING", "SUBMITTED"):
        r.status = d["status"]
    if "scores" in d:
        for s in list(r.scores):
            db.session.delete(s)
        db.session.flush()
        for s in (d["scores"] or []):
            if s.get("criterion"):
                db.session.add(ReviewScore(review_id=r.id, criterion=s["criterion"],
                                           score=float(s.get("score") or 0), weight=int(s.get("weight") or 1)))
        db.session.flush()
        _recalc_overall(r)
    db.session.commit()
    return jsonify({"message": "Đã cập nhật phiếu đánh giá", "overall_score": float(r.overall_score) if r.overall_score is not None else None}), 200


@performance_bp.route("/performance-reviews/<int:rid>", methods=["DELETE"])
@jwt_required()
def delete_review(rid):
    block = _guard()
    if block:
        return block
    r = PerformanceReview.query.filter_by(id=rid, tenant_id=g.tenant_id).first()
    if not r:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200
