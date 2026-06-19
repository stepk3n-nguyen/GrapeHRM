"""
Blueprint Tuyển dụng (Admin/HR): tin tuyển dụng + ứng viên theo luồng phỏng vấn.
"""

from datetime import datetime, date

from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models.recruitment import JobPosting, Candidate
from app.models.employee import Employee, EmployeeSequence
from app.services.audit_service import log_action
from . import recruitment_bp

_STAGE_LABEL = {
    "APPLIED": "Nộp hồ sơ", "INTERVIEW": "Phỏng vấn", "OFFERED": "Mời nhận việc",
    "HIRED": "Trúng tuyển", "REJECTED": "Đã loại",
}
_STAGES = list(_STAGE_LABEL.keys())


def _guard():
    if get_jwt().get("role") not in ("super_admin", "admin", "hr_manager"):
        return jsonify({"error": "Không có quyền truy cập"}), 403
    return None


def _parse(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").date() if d else None
    except (ValueError, TypeError):
        return None


# ── TIN TUYỂN DỤNG ──────────────────────────────────────────────────────
def _serialize_job(j):
    counts = {s: 0 for s in _STAGES}
    for c in j.candidates:
        counts[c.stage] = counts.get(c.stage, 0) + 1
    return {
        "id": j.id, "title": j.title,
        "department_id": j.department_id,
        "department_name": j.department.name if j.department else None,
        "quantity": j.quantity, "description": j.description,
        "status": j.status,
        "posted_date": j.posted_date.isoformat() if j.posted_date else None,
        "total_candidates": len(j.candidates),
        "hired_count": counts.get("HIRED", 0),
        "stage_counts": counts,
    }


@recruitment_bp.route("/job-postings", methods=["GET"])
@jwt_required()
def list_jobs():
    block = _guard()
    if block:
        return block
    items = JobPosting.query.filter_by(tenant_id=g.tenant_id).order_by(JobPosting.id.desc()).all()
    return jsonify([_serialize_job(j) for j in items]), 200


@recruitment_bp.route("/job-postings", methods=["POST"])
@jwt_required()
def create_job():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    if not (d.get("title") or "").strip():
        return jsonify({"error": "Thiếu tiêu đề tin tuyển dụng"}), 400
    j = JobPosting(
        tenant_id=g.tenant_id, title=d["title"].strip(),
        department_id=d.get("department_id") or None,
        quantity=int(d.get("quantity") or 1), description=d.get("description"),
        status=d.get("status", "OPEN"), posted_date=_parse(d.get("posted_date")) or date.today(),
    )
    db.session.add(j)
    db.session.commit()
    return jsonify({"message": "Đã tạo tin tuyển dụng", "id": j.id}), 201


@recruitment_bp.route("/job-postings/<int:jid>", methods=["PUT"])
@jwt_required()
def update_job(jid):
    block = _guard()
    if block:
        return block
    j = JobPosting.query.filter_by(id=jid, tenant_id=g.tenant_id).first()
    if not j:
        return jsonify({"error": "Không tìm thấy"}), 404
    d = request.get_json(silent=True) or {}
    if "title" in d:
        j.title = d["title"].strip() or j.title
    if "department_id" in d:
        j.department_id = d["department_id"] or None
    if "quantity" in d:
        j.quantity = int(d["quantity"] or 1)
    if "description" in d:
        j.description = d["description"]
    if "status" in d:
        j.status = d["status"]
    db.session.commit()
    return jsonify({"message": "Đã cập nhật"}), 200


@recruitment_bp.route("/job-postings/<int:jid>", methods=["DELETE"])
@jwt_required()
def delete_job(jid):
    block = _guard()
    if block:
        return block
    j = JobPosting.query.filter_by(id=jid, tenant_id=g.tenant_id).first()
    if not j:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(j)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


# ── ỨNG VIÊN ────────────────────────────────────────────────────────────
def _serialize_candidate(c):
    return {
        "id": c.id, "job_posting_id": c.job_posting_id,
        "job_title": c.job_posting.title if c.job_posting else None,
        "full_name": c.full_name, "email": c.email, "phone": c.phone,
        "cv_url": c.cv_url, "stage": c.stage, "stage_label": _STAGE_LABEL.get(c.stage, c.stage),
        "note": c.note, "applied_date": c.applied_date.isoformat() if c.applied_date else None,
        "hired_employee_id": c.hired_employee_id,
    }


@recruitment_bp.route("/candidates", methods=["GET"])
@jwt_required()
def list_candidates():
    block = _guard()
    if block:
        return block
    q = Candidate.query.filter_by(tenant_id=g.tenant_id)
    if request.args.get("job_posting_id"):
        q = q.filter_by(job_posting_id=request.args.get("job_posting_id", type=int))
    if request.args.get("stage"):
        q = q.filter_by(stage=request.args.get("stage"))
    items = q.order_by(Candidate.id.desc()).all()
    return jsonify([_serialize_candidate(c) for c in items]), 200


@recruitment_bp.route("/candidates", methods=["POST"])
@jwt_required()
def create_candidate():
    block = _guard()
    if block:
        return block
    d = request.get_json(silent=True) or {}
    job_id = d.get("job_posting_id")
    if not job_id or not (d.get("full_name") or "").strip():
        return jsonify({"error": "Thiếu tin tuyển dụng hoặc tên ứng viên"}), 400
    if not JobPosting.query.filter_by(id=job_id, tenant_id=g.tenant_id).first():
        return jsonify({"error": "Tin tuyển dụng không hợp lệ"}), 400
    c = Candidate(
        tenant_id=g.tenant_id, job_posting_id=job_id, full_name=d["full_name"].strip(),
        email=d.get("email"), phone=d.get("phone"), cv_url=d.get("cv_url"),
        stage=d.get("stage", "APPLIED"), note=d.get("note"),
        applied_date=_parse(d.get("applied_date")) or date.today(),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Đã thêm ứng viên", "id": c.id}), 201


@recruitment_bp.route("/candidates/<int:cid>/stage", methods=["PUT"])
@jwt_required()
def move_stage(cid):
    block = _guard()
    if block:
        return block
    c = Candidate.query.filter_by(id=cid, tenant_id=g.tenant_id).first()
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    stage = (request.get_json(silent=True) or {}).get("stage")
    if stage not in _STAGES:
        return jsonify({"error": "Giai đoạn không hợp lệ"}), 400
    c.stage = stage
    log_action("UPDATE", "CANDIDATE", c.id, details={"stage": stage})
    db.session.commit()
    return jsonify({"message": f"Đã chuyển sang: {_STAGE_LABEL[stage]}"}), 200


@recruitment_bp.route("/candidates/<int:cid>", methods=["DELETE"])
@jwt_required()
def delete_candidate(cid):
    block = _guard()
    if block:
        return block
    c = Candidate.query.filter_by(id=cid, tenant_id=g.tenant_id).first()
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Đã xóa"}), 200


@recruitment_bp.route("/candidates/<int:cid>/hire", methods=["POST"])
@jwt_required()
def hire_candidate(cid):
    """Chuyển ứng viên trúng tuyển thành hồ sơ nhân viên (tạo mã NV mới)."""
    block = _guard()
    if block:
        return block
    c = Candidate.query.filter_by(id=cid, tenant_id=g.tenant_id).first()
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    if c.hired_employee_id:
        return jsonify({"error": "Ứng viên này đã được tuyển"}), 400

    parts = c.full_name.strip().split()
    first_name = " ".join(parts[:-1]) if len(parts) > 1 else c.full_name.strip()
    last_name = parts[-1] if len(parts) > 1 else ""

    seq = EmployeeSequence.query.filter_by(tenant_id=g.tenant_id).first()
    if not seq:
        seq = EmployeeSequence(tenant_id=g.tenant_id, current_value=0)
        db.session.add(seq)
        db.session.flush()
    seq.current_value += 1

    emp = Employee(
        tenant_id=g.tenant_id, employee_id=f"NV-{seq.current_value:03d}",
        first_name=first_name, last_name=last_name,
        work_email=c.email, mobile=c.phone,
        joined_date=date.today(), state="ACTIVE",
        department_id=c.job_posting.department_id if c.job_posting else None,
    )
    db.session.add(emp)
    db.session.flush()

    c.stage = "HIRED"
    c.hired_employee_id = emp.id
    log_action("CREATE", "EMPLOYEE", emp.id, details={"from_candidate": c.id})
    db.session.commit()
    return jsonify({"message": f"Đã tạo nhân viên {emp.employee_id} từ ứng viên", "employee_id": emp.id}), 201
