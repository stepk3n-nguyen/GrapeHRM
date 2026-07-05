"""
Nâng cấp schema tự động cho database CÓ SẴN (idempotent — chạy lại an toàn).

db.create_all() chỉ tạo bảng mới, không sửa bảng cũ. Hàm này bổ sung:
  1. Thêm cột mới vào bảng cũ (attendance.late_minutes/early_minutes,
     employees.shift_id).
  2. Mở rộng ENUM attendance.status thêm EARLY_LEAVE (MySQL).
  3. Xóa các bảng của module đã gỡ khỏi MVP (hợp đồng, tuyển dụng,
     đánh giá hiệu suất).

Với DB mới (create_all từ model) mọi bước đều tự bỏ qua.
"""

from sqlalchemy import inspect, text

from app.extensions import db

# Bảng của các module đã loại khỏi MVP (thứ tự xóa tôn trọng FK)
_DROPPED_TABLES = [
    "review_scores", "performance_reviews", "review_cycles",
    "candidates", "job_postings",
    "contracts",
]

# (bảng, cột, định nghĩa SQL khi ADD COLUMN)
_NEW_COLUMNS = [
    ("attendance", "late_minutes", "INTEGER NOT NULL DEFAULT 0"),
    ("attendance", "early_minutes", "INTEGER NOT NULL DEFAULT 0"),
    ("employees", "shift_id", "INTEGER NULL"),
]


def upgrade_schema():
    insp = inspect(db.engine)
    tables = set(insp.get_table_names())
    is_mysql = db.engine.dialect.name == "mysql"

    # 1. Thêm cột mới
    for table, column, ddl in _NEW_COLUMNS:
        if table not in tables:
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        if column not in existing:
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            print(f"[SCHEMA] Đã thêm cột {table}.{column}")

    # 2. Mở rộng ENUM trạng thái chấm công (chỉ MySQL — SQLite dùng VARCHAR)
    if is_mysql and "attendance" in tables:
        col_type = db.session.execute(text(
            "SELECT COLUMN_TYPE FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'attendance' AND COLUMN_NAME = 'status'"
        )).scalar()
        if col_type and "EARLY_LEAVE" not in str(col_type).upper():
            db.session.execute(text(
                "ALTER TABLE attendance MODIFY COLUMN status "
                "ENUM('PRESENT','ABSENT','LATE','EARLY_LEAVE','HALF_DAY','ON_LEAVE') NOT NULL"
            ))
            print("[SCHEMA] Đã thêm trạng thái EARLY_LEAVE vào attendance.status")

    # 3. FK employees.shift_id → work_shifts (MySQL; SQLite bỏ qua vì DB mới đã có)
    if is_mysql and "employees" in tables:
        # Đã có FK nào trên cột shift_id (bất kể tên) thì bỏ qua
        has_shift_fk = any(
            "shift_id" in (fk.get("constrained_columns") or [])
            for fk in insp.get_foreign_keys("employees")
        )
        if not has_shift_fk:
            try:
                db.session.execute(text(
                    "ALTER TABLE employees ADD CONSTRAINT fk_employees_shift "
                    "FOREIGN KEY (shift_id) REFERENCES work_shifts(id) ON DELETE SET NULL"
                ))
                print("[SCHEMA] Đã thêm FK employees.shift_id → work_shifts.id")
            except Exception:
                db.session.rollback()  # FK có thể đã tồn tại với tên khác

    # 4. Xóa bảng của module đã gỡ
    for table in _DROPPED_TABLES:
        if table in tables:
            db.session.execute(text(f"DROP TABLE {table}"))
            print(f"[SCHEMA] Đã xóa bảng không dùng: {table}")

    db.session.commit()
