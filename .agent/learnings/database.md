# Database

> Tổng hợp kiến thức về cơ sở dữ liệu MySQL 8 và schema design trong dự án GrapeHRM.
> Cập nhật lần cuối: 2026-05-24

---

## Architecture

### Multi-Tenant Data Isolation via tenant_id FK
- **Ngày**: 2026-05-24
- **Chi tiết**: Mọi bảng nghiệp vụ đều chứa cột `tenant_id INT NOT NULL` tham chiếu `tenants(id)`. Đây là cơ chế cách ly dữ liệu giữa các công ty (tenant) trong cùng 1 database vật lý — gọi là **shared-database, shared-schema multi-tenancy**. Mọi query phải luôn lọc theo `tenant_id` (enforce ở tầng middleware Flask, không phải ở SQL).
- **Files liên quan**: `db/schema.sql`

### User–Employee Tách biệt nhưng Liên kết
- **Ngày**: 2026-05-24
- **Chi tiết**: Bảng `users` (xác thực) tách riêng khỏi bảng `employees` (nhân sự). Liên kết qua `users.employee_id` nullable — cho phép super_admin tồn tại mà không cần hồ sơ nhân viên. `UNIQUE(tenant_id, username)` đảm bảo username chỉ duy nhất trong phạm vi 1 tenant.
- **Files liên quan**: `db/schema.sql`

---

## Bugs & Solutions

### Lỗi SQLAlchemy 1054 Unknown column do model out of sync
- **Thời gian**: 2026-05-26
- **Vấn đề**: Khi query model bằng SQLAlchemy báo lỗi `pymysql.err.OperationalError: (1054, "Unknown column 'employees.middle_name' in 'field list'")`.
- **Root cause**: Database đã bị xóa một cột (VD: `middle_name`) nhưng SQLAlchemy Model vẫn còn định nghĩa `middle_name = db.Column(...)`. Khi query (vd: `query.filter_by().first()`), SQLAlchemy tự động SELECT tất cả các cột định nghĩa trong model.
- **Fix**: Xóa định nghĩa cột đó trong Model (VD: `Employee` model) và sửa các logic liên quan (như hàm `full_name()`).
- **Files liên quan**: `app/models/employee.py`

---

## How-To

### Cách khởi tạo database từ Docker lần đầu
- **Ngày**: 2026-05-24
- **Bước thực hiện**:
  1. Đặt file SQL vào `db/` với prefix số thứ tự: `01-schema.sql`, `02-seed.sql`.
  2. Trong `docker-compose.yml`, mount vào `/docker-entrypoint-initdb.d/` — MySQL 8 sẽ tự chạy theo thứ tự alphabet khi container khởi tạo lần đầu.
  3. Nếu volume `mysql_data` đã có dữ liệu cũ, các file init sẽ **KHÔNG** chạy lại. Muốn reset phải xóa volume: `docker-compose down -v`.
- **Files liên quan**: `docker-compose.yml`, `db/schema.sql`, `db/seed.sql`

### Cách seed dữ liệu mặc định an toàn
- **Ngày**: 2026-05-24
- **Bước thực hiện**:
  1. Dùng `INSERT ... ON DUPLICATE KEY UPDATE name=name` để idempotent — chạy lại không lỗi.
  2. Chỉ định `id` cố định cho seed data (vd: tenant id=1) để các FK tham chiếu từ seed khác luôn hợp lệ.
- **Files liên quan**: `db/seed.sql`

---

## Patterns

### ENUM cho Role-Based Access
- **Ngày**: 2026-05-24
- **Chi tiết**: Sử dụng MySQL `ENUM('super_admin','admin','hr_manager','supervisor','employee')` cho cột `users.role`. Ưu điểm: validate tại tầng DB, tiết kiệm storage so với VARCHAR. Nhược điểm: thêm role mới cần ALTER TABLE — chấp nhận được vì role HR ít thay đổi.
- **Ví dụ code**:
  ```sql
  role ENUM('super_admin','admin','hr_manager','supervisor','employee') DEFAULT 'employee'
  ```
- **Files liên quan**: `db/schema.sql`

### Timestamp Columns Convention
- **Ngày**: 2026-05-24
- **Chi tiết**: Quy ước dùng `created_at DATETIME DEFAULT CURRENT_TIMESTAMP` và `updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` cho mọi bảng chính. Bảng phụ (junction table) có thể bỏ qua. MySQL tự quản lý `updated_at` khi row bị UPDATE.
- **Files liên quan**: `db/schema.sql`

### Autoincrement Sequence Generator for Multi-Tenancy
- **Ngày**: 2026-05-26
- **Chi tiết**: Khi cần sinh mã định danh (như `employee_id`) dạng `NV-016` tăng dần và không bao giờ lặp lại (ngay cả khi nhân viên bị xóa), không nên dựa hoàn toàn vào `MAX(id)` hay số lượng nhân viên hiện tại. Thiết kế một bảng `employee_sequences` có khóa chính là `tenant_id` và lưu giữ `current_value` là giải pháp tối ưu. Nó hoạt động như một máy đếm chuỗi độc lập cho mỗi tenant, đảm bảo tính liên tục và cách ly dữ liệu.
- **Files liên quan**: `app/models/employee.py`, `app/employee/routes.py`
