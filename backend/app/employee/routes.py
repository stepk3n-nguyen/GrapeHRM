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
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

def check_hr_admin():
    """Kiểm tra xem user hiện tại có role là admin hoặc hr_manager không."""
    claims = get_jwt()
    return claims.get("role") in ["super_admin", "admin", "hr_manager"]

from app.extensions import db
from app.models.employee import Employee, EmployeeSequence, JobTitle, Department

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
    # Tự động đồng bộ state nếu có end_date
    if emp.end_date:
        from datetime import date
        today = date.today()
        expected_state = "TERMINATED" if emp.end_date <= today else "ACTIVE"
        if emp.state != expected_state:
            emp.state = expected_state
            db.session.commit()
    elif emp.state != "ACTIVE":
        emp.state = "ACTIVE"
        db.session.commit()

    from app.models.user import User
    user_record = User.query.filter_by(employee_id=emp.id).first()

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
        "num_dependents": emp.num_dependents or 0,
        "mobile": emp.mobile,
        "work_email": emp.work_email,
        "joined_date": emp.joined_date.isoformat() if emp.joined_date else None,
        "end_date": emp.end_date.isoformat() if emp.end_date else None,
        "address": emp.address,
        "state": emp.state,
        "profile_pic_url": emp.profile_pic_url,
        "title_id": emp.title_id,
        "title_name": emp.title.name if emp.title else None,
        "department_id": emp.department_id,
        "department_name": emp.department.name if emp.department else None,
        "created_at": emp.created_at.isoformat() if emp.created_at else None,
        "updated_at": emp.updated_at.isoformat() if emp.updated_at else None,
        "role": user_record.role if user_record else None,
        "user_id": user_record.id if user_record else None,
    }


@employee_bp.route("", methods=["GET"])
@jwt_required()
def get_employees():
    """Lấy danh sách tất cả nhân viên của tenant hiện tại."""
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    # Chỉ truy vấn nhân viên thuộc tenant của user đang đăng nhập
    employees = Employee.query.filter_by(tenant_id=tenant_id).order_by(Employee.created_at.desc()).all()
    return jsonify([serialize_employee(emp) for emp in employees]), 200

@employee_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_profile():
    """Lấy thông tin cá nhân của user đang đăng nhập."""
    tenant_id = g.tenant_id
    user_id = get_jwt_identity()
    
    from app.models.user import User
    user = User.query.get(user_id)
    if not user or not user.employee_id:
        return jsonify({"error": "Tài khoản không được liên kết với hồ sơ nhân viên nào"}), 404

    emp = Employee.query.filter_by(id=user.employee_id, tenant_id=tenant_id).first()
    if not emp:
        return jsonify({"error": "Không tìm thấy hồ sơ nhân viên"}), 404

    return jsonify(serialize_employee(emp)), 200


@employee_bp.route("/next-id", methods=["GET"])
@jwt_required()
def get_next_employee_id_route():
    """Lấy mã nhân sự tiếp theo (dành cho việc tạo mới)."""
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

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
    if not check_hr_admin():
        return jsonify({"error": "Không có quyền truy cập"}), 403

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
    end_date = parse_date(data.get("end_date"))
    address = data.get("address", "").strip() or None
    
    state = "ACTIVE"
    if end_date:
        from datetime import date
        if end_date <= date.today():
            state = "TERMINATED"

    profile_pic_url = data.get("profile_pic_url", "").strip() or None
    
    title_id = data.get("title_id")
    if title_id is not None:
        try:
            title_id = int(title_id) if title_id else None
        except ValueError:
            title_id = None
            
    department_id = data.get("department_id")
    if department_id is not None:
        try:
            department_id = int(department_id) if department_id else None
        except ValueError:
            department_id = None

    try:
        num_dependents = int(data.get("num_dependents") or 0)
    except (ValueError, TypeError):
        num_dependents = 0

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
        end_date=end_date,
        address=address,
        state=state,
        profile_pic_url=profile_pic_url,
        title_id=title_id,
        department_id=department_id,
        num_dependents=max(num_dependents, 0),
    )

    db.session.add(new_emp)
    db.session.flush()

    # Create associated User account
    role = data.get("role", "employee")
    from app.models.user import User
    username = new_emp.employee_id.replace("-", "").lower() if new_emp.employee_id else f"nv{new_emp.id}"
    
    new_user = User(
        tenant_id=tenant_id,
        employee_id=new_emp.id,
        username=username,
        email=work_email or f"{username}@grapecorp.com",
        role=role,
        is_active=True
    )
    new_user.set_password("123456")
    db.session.add(new_user)

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
    if "end_date" in data:
        emp.end_date = parse_date(data.get("end_date"))
    if "address" in data:
        emp.address = data.get("address", "").strip() or None
        
    # Auto calc state
    if emp.end_date:
        from datetime import date
        emp.state = "TERMINATED" if emp.end_date <= date.today() else "ACTIVE"
    else:
        emp.state = "ACTIVE"

    if "num_dependents" in data:
        try:
            emp.num_dependents = max(int(data.get("num_dependents") or 0), 0)
        except (ValueError, TypeError):
            pass
    if "profile_pic_url" in data:
        emp.profile_pic_url = data.get("profile_pic_url", "").strip() or None
    if "title_id" in data:
        t_id = data.get("title_id")
        try:
            emp.title_id = int(t_id) if t_id else None
        except ValueError:
            pass
    if "department_id" in data:
        d_id = data.get("department_id")
        try:
            emp.department_id = int(d_id) if d_id else None
        except ValueError:
            pass

    db.session.flush()

    # Handle role update if user is admin
    role = data.get("role")
    if role and get_jwt().get("role") == "admin":
        from app.models.user import User
        user = User.query.filter_by(employee_id=emp.id).first()
        if user:
            user.role = role
        else:
            username = emp.employee_id.replace("-", "").lower() if emp.employee_id else f"nv{emp.id}"
            user = User(
                tenant_id=tenant_id,
                employee_id=emp.id,
                username=username,
                email=emp.work_email or f"{username}@grapecorp.com",
                role=role,
                is_active=True
            )
            user.set_password("123456")
            db.session.add(user)

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


# ── BLUEPRINT & ENDPOINTS CHO QUẢN LÝ CHỨC VỤ (JOB TITLE) ─────

title_bp = Blueprint("title", __name__, url_prefix="/api/job-titles")


def serialize_title(pos):
    return {
        "id": pos.id,
        "tenant_id": pos.tenant_id,
        "name": pos.name,
        "description": pos.description,
        "created_at": pos.created_at.isoformat() if pos.created_at else None,
    }


@title_bp.route("", methods=["GET"])
@jwt_required()
def get_titles():
    """Lấy danh sách tất cả chức vụ của tenant."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    titles = JobTitle.query.filter_by(tenant_id=tenant_id).order_by(JobTitle.name.asc()).all()
    return jsonify([serialize_title(t) for t in titles]), 200


@title_bp.route("", methods=["POST"])
@jwt_required()
def create_title():
    """Thêm mới một chức vụ cho tenant."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    data = request.get_json(silent=True)
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Tên chức vụ là bắt buộc"}), 400

    name = data.get("name").strip()
    description = data.get("description", "").strip() or None

    # Kiểm tra trùng tên trong cùng tenant
    existing = JobTitle.query.filter_by(tenant_id=tenant_id, name=name).first()
    if existing:
        return jsonify({"error": "Chức vụ này đã tồn tại"}), 400

    new_pos = JobTitle(
        tenant_id=tenant_id,
        name=name,
        description=description,
    )
    db.session.add(new_pos)
    db.session.commit()

    return jsonify({
        "message": "Thêm chức vụ thành công",
        "title": serialize_title(new_pos)
    }), 201


@title_bp.route("/<int:pos_id>", methods=["PUT"])
@jwt_required()
def update_title(pos_id):
    """Cập nhật tên hoặc mô tả chức vụ."""
    tenant_id = g.tenant_id
    pos = JobTitle.query.filter_by(id=pos_id, tenant_id=tenant_id).first()
    if not pos:
        return jsonify({"error": "Không tìm thấy chức vụ"}), 404

    data = request.get_json(silent=True)
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Tên chức vụ là bắt buộc"}), 400

    name = data.get("name").strip()
    description = data.get("description", "").strip() or None

    # Kiểm tra trùng tên với các vị trí khác
    existing = JobTitle.query.filter_by(tenant_id=tenant_id, name=name).filter(JobTitle.id != pos_id).first()
    if existing:
        return jsonify({"error": "Chức vụ với tên này đã tồn tại"}), 400

    pos.name = name
    pos.description = description
    db.session.commit()

    return jsonify({
        "message": "Cập nhật chức vụ thành công",
        "title": serialize_title(pos)
    }), 200


@title_bp.route("/<int:pos_id>", methods=["DELETE"])
@jwt_required()
def delete_title(pos_id):
    """Xóa chức vụ khỏi hệ thống."""
    tenant_id = g.tenant_id
    pos = JobTitle.query.filter_by(id=pos_id, tenant_id=tenant_id).first()
    if not pos:
        return jsonify({"error": "Không tìm thấy chức vụ"}), 404

    db.session.delete(pos)
    db.session.commit()

    return jsonify({"message": "Xóa chức vụ thành công"}), 200


# ── BLUEPRINT & ENDPOINTS CHO QUẢN LÝ PHÒNG BAN (DEPARTMENT) ─────

department_bp = Blueprint("department", __name__, url_prefix="/api/departments")

def serialize_department(dept):
    return {
        "id": dept.id,
        "tenant_id": dept.tenant_id,
        "name": dept.name,
        "description": dept.description,
        "created_at": dept.created_at.isoformat() if dept.created_at else None,
    }

@department_bp.route("", methods=["GET"])
@jwt_required()
def get_departments():
    """Lấy danh sách tất cả phòng ban của tenant."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    departments = Department.query.filter_by(tenant_id=tenant_id).order_by(Department.name.asc()).all()
    return jsonify([serialize_department(d) for d in departments]), 200

@department_bp.route("", methods=["POST"])
@jwt_required()
def create_department():
    """Thêm mới phòng ban."""
    tenant_id = g.tenant_id
    if not tenant_id:
        return jsonify({"error": "Không xác định được Tenant ID"}), 403

    data = request.get_json(silent=True)
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Tên phòng ban là bắt buộc"}), 400

    name = data.get("name").strip()
    description = data.get("description", "").strip() or None

    existing = Department.query.filter_by(tenant_id=tenant_id, name=name).first()
    if existing:
        return jsonify({"error": "Phòng ban này đã tồn tại"}), 400

    new_dept = Department(tenant_id=tenant_id, name=name, description=description)
    db.session.add(new_dept)
    db.session.commit()

    return jsonify({
        "message": "Thêm phòng ban thành công",
        "department": serialize_department(new_dept)
    }), 201

@department_bp.route("/<int:dept_id>", methods=["PUT"])
@jwt_required()
def update_department(dept_id):
    """Cập nhật phòng ban."""
    tenant_id = g.tenant_id
    dept = Department.query.filter_by(id=dept_id, tenant_id=tenant_id).first()
    if not dept:
        return jsonify({"error": "Không tìm thấy phòng ban"}), 404

    data = request.get_json(silent=True)
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Tên phòng ban là bắt buộc"}), 400

    name = data.get("name").strip()
    description = data.get("description", "").strip() or None

    existing = Department.query.filter_by(tenant_id=tenant_id, name=name).filter(Department.id != dept_id).first()
    if existing:
        return jsonify({"error": "Tên phòng ban này đã tồn tại"}), 400

    dept.name = name
    dept.description = description
    db.session.commit()

    return jsonify({
        "message": "Cập nhật phòng ban thành công",
        "department": serialize_department(dept)
    }), 200

@department_bp.route("/<int:dept_id>", methods=["DELETE"])
@jwt_required()
def delete_department(dept_id):
    """Xóa phòng ban."""
    tenant_id = g.tenant_id
    dept = Department.query.filter_by(id=dept_id, tenant_id=tenant_id).first()
    if not dept:
        return jsonify({"error": "Không tìm thấy phòng ban"}), 404

    db.session.delete(dept)
    db.session.commit()

    return jsonify({"message": "Xóa phòng ban thành công"}), 200
