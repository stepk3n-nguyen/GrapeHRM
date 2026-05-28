"""
Blueprint Employee — Xử lý các thao tác CRUD nhân sự của từng tenant.
Endpoints:
    GET    /api/employees       — Lấy danh sách nhân viên của tenant
    POST   /api/employees       — Tạo nhân viên mới cho tenant
    GET    /api/employees/<id>  — Lấy thông tin chi tiết một nhân viên
    PUT    /api/employees/<id>  — Cập nhật thông tin nhân viên
    DELETE /api/employees/<id>  — Xóa nhân viên khỏi hệ thống
"""

from datetime import datetime
import re
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.employee import Employee, EmployeeSequence, JobPosition

employee_bp = Blueprint("employee", __name__, url_prefix="/api/employees")


def generate_next_employee_id(tenant_id):
    """
    Tự động sinh mã nhân viên tăng dần: NV-016, NV-017...
    Bất kể nhân viên bị xóa, mã mới vẫn tiếp tục tăng dần dựa trên bảng employee_sequences.
    """
    # 1. Tìm bản ghi sequence cho tenant này
    seq = EmployeeSequence.query.filter_by(tenant_id=tenant_id).first()
    if not seq:
        # Nếu chưa có, quét các nhân viên cũ của tenant để tìm số lớn nhất
        # nhằm duy trì tính liên tục (bắt đầu từ 15 nếu hiện tại có NV-15)
        employees = Employee.query.filter_by(tenant_id=tenant_id).all()
        max_val = 0
        for emp in employees:
            if emp.employee_id and emp.employee_id.startswith("NV-"):
                try:
                    # Trích xuất toàn bộ chữ số
                    num_part = re.sub(r"\D", "", emp.employee_id)
                    val = int(num_part) if num_part else 0
                    if val > max_val:
                        max_val = val
                except ValueError:
                    pass

        # Tạo mới sequence
        seq = EmployeeSequence(tenant_id=tenant_id, current_value=max_val)
        db.session.add(seq)
        db.session.flush()

    # 2. Tăng giá trị sequence lên 1
    seq.current_value += 1
    db.session.add(seq)

    # Định dạng NV-XXX (tối thiểu 3 chữ số, ví dụ NV-016)
    return f"NV-{seq.current_value:03d}"


def parse_date(date_str):
    """Chuyển đổi string định dạng YYYY-MM-DD thành đối tượng date."""
    if not date_str:
        return None
    try:
        # Nhận vào format 'YYYY-MM-DD' hoặc ISO string ngắn
        return datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
    except (ValueError, IndexError):
        return None


def serialize_employee(emp):
    """Serialize đối tượng Employee thành dictionary JSON-friendly."""
    return {
        "id": emp.id,
        "tenant_id": emp.tenant_id,
        "employee_id": emp.employee_id,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "full_name": emp.full_name(),
        "gender": emp.gender,
        "marital_status": emp.marital_status,
        "birthday": emp.birthday.isoformat() if emp.birthday else None,
        "mobile": emp.mobile,
        "work_email": emp.work_email,
        "joined_date": emp.joined_date.isoformat() if emp.joined_date else None,
        "state": emp.state,
        "profile_pic_url": emp.profile_pic_url,
        "position_id": emp.position_id,
        "position_name": emp.position.name if emp.position else None,
        "created_at": emp.created_at.isoformat() if emp.created_at else None,
        "updated_at": emp.updated_at.isoformat() if emp.updated_at else None,
    }


@employee_bp.route("", methods=["GET"])
@jwt_required()
def get_employees():
    """Lấy danh sách tất cả nhân viên của tenant hiện tại."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    # Chỉ truy vấn nhân viên thuộc tenant của user đang đăng nhập
    employees = Employee.query.filter_by(tenant_id=tenant_id).order_by(Employee.created_at.desc()).all()
    return jsonify([serialize_employee(emp) for emp in employees]), 200


@employee_bp.route("/next-id", methods=["GET"])
@jwt_required()
def get_next_employee_id_route():
    """Lấy mã nhân sự tiếp theo (dành cho việc tạo mới)."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    seq = EmployeeSequence.query.filter_by(tenant_id=tenant_id).first()
    next_val = 1
    if seq:
        next_val = seq.current_value + 1
    else:
        # Nếu chưa có sequence, quét từ DB để lấy mã lớn nhất
        employees = Employee.query.filter_by(tenant_id=tenant_id).all()
        max_val = 0
        for emp in employees:
            if emp.employee_id and emp.employee_id.startswith("NV-"):
                try:
                    num_part = re.sub(r"\D", "", emp.employee_id)
                    val = int(num_part) if num_part else 0
                    if val > max_val:
                        max_val = val
                except ValueError:
                    pass
        next_val = max_val + 1

    return jsonify({"next_id": f"NV-{next_val:03d}"}), 200


@employee_bp.route("", methods=["POST"])
@jwt_required()
def create_employee():
    """Tạo mới một nhân sự cho tenant."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Thiếu dữ liệu gửi lên"}), 400

    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()

    if not first_name or not last_name:
        return jsonify({"error": "Họ (first_name) và Tên (last_name) là bắt buộc"}), 400

    # Lấy các trường thông tin khác từ request
    employee_id = data.get("employee_id", "").strip() or None
    if not employee_id:
        employee_id = generate_next_employee_id(tenant_id)
    gender = data.get("gender")
    if gender is not None:
        try:
            gender = int(gender)
        except ValueError:
            gender = None

    marital_status = data.get("marital_status", "").strip() or None
    birthday = parse_date(data.get("birthday"))
    mobile = data.get("mobile", "").strip() or None
    work_email = data.get("work_email", "").strip() or None
    joined_date = parse_date(data.get("joined_date"))
    state = data.get("state", "ACTIVE")
    if state not in ("ACTIVE", "TERMINATED"):
        state = "ACTIVE"
    profile_pic_url = data.get("profile_pic_url", "").strip() or None
    position_id = data.get("position_id")
    if position_id is not None:
        try:
            position_id = int(position_id) if position_id else None
        except ValueError:
            position_id = None

    new_emp = Employee(
        tenant_id=tenant_id,
        employee_id=employee_id,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        marital_status=marital_status,
        birthday=birthday,
        mobile=mobile,
        work_email=work_email,
        joined_date=joined_date,
        state=state,
        profile_pic_url=profile_pic_url,
        position_id=position_id,
    )

    db.session.add(new_emp)
    db.session.commit()

    return jsonify({
        "message": "Tạo nhân sự thành công",
        "employee": serialize_employee(new_emp)
    }), 201


@employee_bp.route("/<int:emp_id>", methods=["GET"])
@jwt_required()
def get_employee_detail(emp_id):
    """Lấy thông tin chi tiết một nhân viên (phải thuộc tenant)."""
    tenant_id = g.tenant_id
    emp = Employee.query.filter_by(id=emp_id, tenant_id=tenant_id).first()

    if not emp:
        return jsonify({"error": "Không tìm thấy hồ sơ nhân viên"}), 404

    return jsonify(serialize_employee(emp)), 200


@employee_bp.route("/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    """Cập nhật thông tin nhân viên (phải thuộc tenant)."""
    tenant_id = g.tenant_id
    emp = Employee.query.filter_by(id=emp_id, tenant_id=tenant_id).first()

    if not emp:
        return jsonify({"error": "Không tìm thấy hồ sơ nhân viên"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Thiếu dữ liệu cập nhật"}), 400

    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()

    if first_name:
        emp.first_name = first_name
    if last_name:
        emp.last_name = last_name

    # Cập nhật các trường còn lại nếu có truyền lên
    if "employee_id" in data:
        emp.employee_id = data.get("employee_id", "").strip() or None
    if "gender" in data:
        gender = data.get("gender")
        emp.gender = int(gender) if gender is not None else None
    if "marital_status" in data:
        emp.marital_status = data.get("marital_status", "").strip() or None
    if "birthday" in data:
        emp.birthday = parse_date(data.get("birthday"))
    if "mobile" in data:
        emp.mobile = data.get("mobile", "").strip() or None
    if "work_email" in data:
        emp.work_email = data.get("work_email", "").strip() or None
    if "joined_date" in data:
        emp.joined_date = parse_date(data.get("joined_date"))
    if "state" in data:
        state = data.get("state")
        if state in ("ACTIVE", "TERMINATED"):
            emp.state = state
    if "profile_pic_url" in data:
        emp.profile_pic_url = data.get("profile_pic_url", "").strip() or None
    if "position_id" in data:
        pos_id = data.get("position_id")
        try:
            emp.position_id = int(pos_id) if pos_id else None
        except ValueError:
            pass

    db.session.commit()

    return jsonify({
        "message": "Cập nhật nhân viên thành công",
        "employee": serialize_employee(emp)
    }), 200


@employee_bp.route("/<int:emp_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(emp_id):
    """Xóa nhân viên khỏi hệ thống (phải thuộc tenant)."""
    tenant_id = g.tenant_id
    emp = Employee.query.filter_by(id=emp_id, tenant_id=tenant_id).first()

    if not emp:
        return jsonify({"error": "Không tìm thấy hồ sơ nhân viên"}), 404

    # Thực hiện hard delete record nhân sự
    db.session.delete(emp)
    db.session.commit()

    return jsonify({"message": "Xóa nhân sự thành công"}), 200


# ── BLUEPRINT & ENDPOINTS CHO QUẢN LÝ VỊ TRÍ CÔNG VIỆC (JOB POSITION) ─────

position_bp = Blueprint("position", __name__, url_prefix="/api/positions")


def serialize_position(pos):
    return {
        "id": pos.id,
        "tenant_id": pos.tenant_id,
        "name": pos.name,
        "description": pos.description,
        "created_at": pos.created_at.isoformat() if pos.created_at else None,
    }


@position_bp.route("", methods=["GET"])
@jwt_required()
def get_positions():
    """Lấy danh sách tất cả vị trí công việc của tenant."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    positions = JobPosition.query.filter_by(tenant_id=tenant_id).order_by(JobPosition.name.asc()).all()
    return jsonify([serialize_position(pos) for pos in positions]), 200


@position_bp.route("", methods=["POST"])
@jwt_required()
def create_position():
    """Thêm mới một vị trí công việc cho tenant."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    data = request.get_json(silent=True)
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Tên vị trí công việc là bắt buộc"}), 400

    name = data.get("name").strip()
    description = data.get("description", "").strip() or None

    # Kiểm tra trùng tên trong cùng tenant
    existing = JobPosition.query.filter_by(tenant_id=tenant_id, name=name).first()
    if existing:
        return jsonify({"error": "Vị trí công việc này đã tồn tại"}), 400

    new_pos = JobPosition(
        tenant_id=tenant_id,
        name=name,
        description=description,
    )
    db.session.add(new_pos)
    db.session.commit()

    return jsonify({
        "message": "Thêm vị trí công việc thành công",
        "position": serialize_position(new_pos)
    }), 201


@position_bp.route("/<int:pos_id>", methods=["PUT"])
@jwt_required()
def update_position(pos_id):
    """Cập nhật tên hoặc mô tả vị trí công việc."""
    tenant_id = g.tenant_id
    pos = JobPosition.query.filter_by(id=pos_id, tenant_id=tenant_id).first()
    if not pos:
        return jsonify({"error": "Không tìm thấy vị trí công việc"}), 404

    data = request.get_json(silent=True)
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Tên vị trí công việc là bắt buộc"}), 400

    name = data.get("name").strip()
    description = data.get("description", "").strip() or None

    # Kiểm tra trùng tên với các vị trí khác
    existing = JobPosition.query.filter_by(tenant_id=tenant_id, name=name).filter(JobPosition.id != pos_id).first()
    if existing:
        return jsonify({"error": "Vị trí công việc với tên này đã tồn tại"}), 400

    pos.name = name
    pos.description = description
    db.session.commit()

    return jsonify({
        "message": "Cập nhật vị trí công việc thành công",
        "position": serialize_position(pos)
    }), 200


@position_bp.route("/<int:pos_id>", methods=["DELETE"])
@jwt_required()
def delete_position(pos_id):
    """Xóa vị trí công việc khỏi hệ thống (soft/hard delete)."""
    tenant_id = g.tenant_id
    pos = JobPosition.query.filter_by(id=pos_id, tenant_id=tenant_id).first()
    if not pos:
        return jsonify({"error": "Không tìm thấy vị trí công việc"}), 404

    db.session.delete(pos)
    db.session.commit()

    return jsonify({"message": "Xóa vị trí công việc thành công"}), 200
