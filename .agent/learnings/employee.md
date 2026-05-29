# Employee Management

> Tổng hợp kiến thức về Quản lý nhân viên (đặc biệt là hiển thị STT, format mã NV, tích hợp Vị trí công việc và tinh chỉnh UI) trong dự án.
> Cập nhật lần cuối: 2026-05-30 | 03:45:00

---

## Architecture

### Quyết định lưu trữ Số thứ tự (STT)
- **Thời gian**: 2026-05-27 | 17:05:00
- **Chi tiết**: Quyết định không lưu cột `serial` (hay STT) vào Database. Việc đánh số thứ tự cho nhân viên chỉ mang tính chất hiển thị, dễ thay đổi khi lọc/tìm kiếm hoặc xóa nhân sự. Do đó, logic này nên được thực hiện hoàn toàn ở phía Frontend thông qua index của mảng thay vì persist xuống backend.
- **Files liên quan**: `frontend/src/pages/EmployeePage.jsx`, `backend/app/models/employee.py`

### Tích hợp JobPosition và Employee cô lập multi-tenant
- **Thời gian**: 2026-05-29 | 02:31:00
- **Chi tiết**: Quyết định liên kết bảng `employees` và `job_positions` với khóa ngoại `position_id` sử dụng ràng buộc `ondelete="SET NULL"`. Việc này đảm bảo khi một Vị trí bị admin xóa, các nhân viên đang giữ vị trí đó sẽ được tự động chuyển về `NULL` một cách an toàn thay vì bị xóa hàng loạt hoặc gây lỗi ràng buộc. Cả hai thực thể đều kế thừa `TenantMixin` để đảm bảo cô lập dữ liệu tuyệt đối giữa các tenant qua JWT.
- **Files liên quan**: `backend/app/models/employee.py`, `backend/app/employee/routes.py`

### Tự động tính toán Trạng thái (Computed State)
- **Thời gian**: 2026-05-30 | 03:45:00
- **Chi tiết**: Thay vì bắt người dùng tự chọn trạng thái "Đang làm" hay "Đã nghỉ", hệ thống thiết kế trường `state` tự động tính toán từ `end_date`. Tại thời điểm lưu (POST/PUT) và thời điểm serialize (GET), hệ thống so sánh `end_date <= date.today()` để quyết định giá trị `TERMINATED` hay `ACTIVE`. Thiết kế này đảm bảo dữ liệu luôn chính xác theo thời gian thực mà không cần viết cronjob.
- **Files liên quan**: `backend/app/employee/routes.py`

---

## Bugs & Solutions

### Lỗi "Unknown column 'serial'" khi fetch danh sách
- **Thời gian**: 2026-05-27 | 17:05:00
- **Vấn đề**: Sau khi thêm field `serial = db.Column(...)` vào model `Employee` và query, SQLAlchemy tự động map column này vào câu lệnh SELECT, nhưng dưới Database MySQL thực tế chưa có cột này (chưa chạy migration/alembic).
- **Root cause**: Database schema lệch pha với SQLAlchemy Model.
- **Fix**: Revert model về trạng thái ban đầu, loại bỏ `serial`. Đẩy logic tạo số thứ tự lên Frontend.
- **Files liên quan**: `backend/app/employee/routes.py`, `backend/app/models/employee.py`

### Lỗi schema không đồng bộ khi dùng db.create_all()
- **Thời gian**: 2026-05-29 | 02:31:00
- **Vấn đề**: SQLAlchemy `db.create_all()` được kích hoạt khi khởi động lại backend chỉ tạo các bảng mới chưa tồn tại (`job_positions`), nhưng không tự động thêm cột mới (`position_id`) vào các bảng đã tồn tại sẵn (`employees`), dẫn tới lỗi `Unknown column` khi gọi API.
- **Root cause**: `db.create_all()` không tự động sinh các lệnh `ALTER TABLE` cho bảng đã tồn tại.
- **Fix**: Chạy thủ công câu lệnh SQL `ALTER TABLE employees ADD COLUMN position_id INT NULL;` và thêm khóa ngoại liên kết tới bảng vị trí để đồng bộ ngay lập tức.
- **Files liên quan**: `backend/app/models/employee.py`

### Lỗi cú pháp JSX do thiếu thẻ đóng và ngoặc kết thúc hàm
- **Thời gian**: 2026-05-29 | 02:31:00
- **Vấn đề**: Gặp lỗi `Unexpected token` và `Expected corresponding JSX closing tag` khiến Vite biên dịch thất bại hoàn toàn.
- **Root cause**: Khi thay thế code ở phần upload ảnh đại diện của biểu mẫu, các thẻ đóng `div` và ngoặc nhọn đóng hàm Javascript `}}` của thuộc tính `onChange` bị cắt bỏ nhầm.
- **Fix**: Đưa file về phiên bản ổn định gần nhất trên Git (HEAD) và áp dụng lại các thay đổi một cách cẩn thận, cân đối các thẻ mở và đóng JSX/Javascript.
- **Files liên quan**: `frontend/src/pages/EmployeePage.jsx`

---

## How-To

### Format lại hàng loạt Mã Nhân viên (ID) bằng SQL
- **Thời gian**: 2026-05-27 | 17:05:00
- **Bước thực hiện**:
  1. Khi cần sửa format cũ từ `NV-01` sang chuẩn `NV-001`, có thể dùng MySQL queries thao tác trực tiếp thay vì viết script Python.
  2. Dùng hàm `SUBSTRING` để cắt bỏ tiền tố "NV-".
  3. Dùng `LPAD(..., 3, '0')` để đệm số 0 cho đủ 3 ký tự.
  4. Nối lại bằng `CONCAT`.
- **Câu lệnh mẫu**:
  ```sql
  UPDATE employees 
  SET employee_id = CONCAT('NV-', LPAD(SUBSTRING(employee_id, 4), 3, '0')) 
  WHERE employee_id LIKE 'NV-%';
  ```

### Tự động preview Mã nhân sự không làm tăng sequence
- **Thời gian**: 2026-05-29 | 02:31:00
- **Bước thực hiện**:
  1. Ở Backend, xây dựng endpoint `/api/employees/next-id` để chỉ đọc sequence hiện tại của Tenant và định dạng chuỗi preview `NV-XXX` mà không gọi `commit` tăng sequence trong database. Việc này tránh nhảy số sequence khi người dùng mở form rồi nhấn Cancel (Hủy bỏ).
  2. Ở Frontend, khi mở modal Thêm mới, gọi API trên để lấy mã preview và gán trực tiếp vào form state.
  3. Đặt thuộc tính `disabled` và style `backgroundColor: '#e9ecef'; cursor: 'not-allowed';` cho trường Mã nhân sự để khóa quyền chỉnh sửa của người dùng.
- **Files liên quan**: `backend/app/employee/routes.py`, `frontend/src/pages/EmployeePage.jsx`

---

## Patterns

### Hiển thị STT động trong React Table
- **Thời gian**: 2026-05-27 | 17:05:00
- **Chi tiết**: Trong React, thay vì sử dụng ID hoặc dữ liệu từ backend để làm STT, sử dụng chính `index + 1` của hàm `.map()` sau khi array đã được filter/sort. Pattern này đảm bảo STT luôn tuyến tính 1, 2, 3... trên giao diện bất kể user search hay paginate.
- **Ví dụ code**:
  ```javascript
  {filteredEmployees.map((emp, index) => (
    <tr key={emp.id}>
      <td>{index + 1}</td>
      {/* ...other columns */}
    </tr>
  ))}
  ```
- **Files liên quan**: `frontend/src/pages/EmployeePage.jsx`

### CSS Modifier để loại bỏ hiệu ứng hover Card BEM
- **Thời gian**: 2026-05-29 | 02:31:00
- **Chi tiết**: Khi một component (như `.card`) có hiệu ứng hover nâng lên mặc định (`transform: translateY(-2px); box-shadow: var(--shadow-md);`) nhưng cần loại bỏ hiệu ứng này cho một thực thể cụ thể (như bảng danh sách cố định), sử dụng class modifier `.card--no-hover` để ghi đè thuộc tính hover.
- **Ví dụ code**:
  ```css
  .card--no-hover:hover {
    box-shadow: var(--shadow-sm);
    transform: none;
  }
  ```
- **Files liên quan**: `frontend/src/assets/css/index.css`, `frontend/src/pages/EmployeePage.jsx`

### Cấu trúc Grid 3 Cột cho Form Layout
- **Thời gian**: 2026-05-30 | 03:45:00
- **Chi tiết**: Để tối ưu không gian hiển thị form nhập liệu ngang, sử dụng CSS Grid thay vì Flexbox để chia form thành 3 cột đều nhau. Responsive cho màn hình nhỏ bằng cách đổi `grid-template-columns` về `1fr`.
- **Ví dụ code**:
  ```css
  .form-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  @media (max-width: 768px) { .form-grid-3 { grid-template-columns: 1fr; } }
  ```
- **Files liên quan**: `frontend/src/pages/EmployeePage.jsx`
