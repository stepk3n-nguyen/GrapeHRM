# Patterns

> Tổng hợp các design pattern, coding convention, và best practices trong dự án GrapeHRM.
> Cập nhật lần cuối: 2026-05-24

---

### SQLAlchemy Mixin Pattern cho Multi-Tenancy và Timestamp
- **Ngày**: 2026-05-24
- **Task**: Xây dựng Backend Models (`User`, `Employee`)
- **Chi tiết**: Sử dụng `TenantMixin` và `TimestampMixin` để tái sử dụng cấu trúc cho các bảng nghiệp vụ. Bất kỳ model nào kế thừa `TenantMixin` sẽ tự động có cột `tenant_id` và khóa ngoại trỏ về `tenants`. Việc này đảm bảo tính nhất quán và giảm lặp code đáng kể.
- **Files liên quan**: `app/models/base.py`, `app/models/user.py`, `app/models/employee.py`

### Password Hashing với Bcrypt trong Model
- **Ngày**: 2026-05-24
- **Task**: Xây dựng Model User
- **Chi tiết**: Đóng gói (Encapsulate) logic mã hóa mật khẩu trực tiếp bên trong Model `User` bằng 2 hàm `set_password` và `check_password` dùng thư viện `bcrypt`. Pattern này tuân thủ nguyên tắc "Fat Model - Thin Controller", giúp các hàm xử lý API Auth gọn gàng hơn và tránh lặp logic hash mật khẩu ở nhiều nơi.
- **Files liên quan**: `app/models/user.py`

### Đảm bảo Unique Constraint trong kiến trúc Multi-Tenant
- **Ngày**: 2026-05-24
- **Task**: Xây dựng Model User
- **Chi tiết**: Trong mô hình shared-database multi-tenancy, tuyệt đối không dùng `unique=True` đơn lẻ cho các cột như `username` (vì 2 công ty khác nhau hoàn toàn có thể trùng username "admin"). Thay vào đó, phải dùng `__table_args__ = (db.UniqueConstraint("tenant_id", "username"),)` để giới hạn tính duy nhất (unique) kết hợp theo từng tenant.
- **Files liên quan**: `app/models/user.py`
