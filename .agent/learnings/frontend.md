# Frontend & Employee CRUD Integration

> Tổng hợp kiến thức về việc khởi tạo dự án Frontend bằng Vite React, tích hợp hệ thống BEM CSS Design System cao cấp và thiết lập API REST CRUD Nhân sự multi-tenant trong GrapeHRM.
> Cập nhật lần cuối: 2026-05-25 | 19:40:00

---

## Architecture

### Kiến trúc Tích hợp Frontend Vite và Backend Flask qua Proxy
- **Thời gian**: 2026-05-25 | 19:40:00
- **Chi tiết**: Để tránh các lỗi liên quan đến CORS (Cross-Origin Resource Sharing) trong quá trình phát triển cục bộ và đảm bảo tính đồng bộ bảo mật, chúng ta cấu hình máy chủ phát triển Vite phát chạy trên port 3000 và sử dụng cơ chế proxy tích hợp để chuyển tiếp mọi request có tiền tố `/api` trực tiếp về Flask container (`http://api:5000`) trên mạng nội bộ Docker.
- **Files liên quan**: `frontend/vite.config.js`, `docker-compose.yml`

### Quản lý Trạng thái Xác thực bằng React Context API
- **Thời gian**: 2026-05-25 | 19:40:00
- **Chi tiết**: Sử dụng React Context làm "màng bảo vệ" (Route Guard) toàn cục. `AuthContext` quản lý `token` lưu trữ trong `localStorage` và tự động khôi phục thông tin cá nhân `user` thông qua API `/api/auth/me` khi tải trang. Giao diện chính của ứng dụng chỉ được kết xuất (render) khi token hợp lệ, ngược lại sẽ redirect về `LoginPage`.
- **Files liên quan**: `frontend/src/context/AuthContext.jsx`, `frontend/src/App.jsx`

### Thiết kế Đồng bộ hóa Trạng thái Sidebar và Co dãn Workspace
- **Thời gian**: 2026-05-28 | 04:15:00
- **Chi tiết**: Đồng bộ hóa state `isSidebarOpen` giữa `<Sidebar>` (trượt ẩn/hiện) và `<main className="app__workspace">` (co dãn nội dung) trên desktop. Trạng thái được khởi tạo động bằng `window.innerWidth > 768` (mở mặc định trên Desktop, đóng trên Mobile). Khi toggle, sidebar dùng `transform: translateX(-100%)` cùng transition mượt mà, đồng thời workspace thay đổi `margin-left` tạo hiệu ứng mở rộng cực kỳ tự nhiên.
- **Files liên quan**: `frontend/src/App.jsx`, `frontend/src/components/Sidebar.jsx`, `frontend/src/assets/css/index.css`

---

## Bugs & Solutions

### Lỗi Parse JSON khi Server Phản hồi Lỗi 500 HTML
- **Thời gian**: 2026-05-25 | 19:40:00
- **Vấn đề**: Khi Backend gặp sự cố và trả về lỗi `500 Internal Server Error`, nội dung phản hồi là trang HTML báo lỗi của Flask. Frontend gọi `await response.json()` bị lỗi cú pháp parser, tự động ném ngoại lệ làm crash ứng dụng và kích hoạt thông báo sai lệch là *"Không thể kết nối đến máy chủ"*.
- **Root cause**: Frontend mặc định giả định mọi phản hồi (ngay cả khi thất bại) đều là JSON, dẫn đến parse HTML lỗi.
- **Fix**: Sử dụng cơ chế kiểm tra Header phản hồi: Chỉ gọi `await response.json()` nếu header `Content-Type` chứa chuỗi `application/json`. Đồng thời hiển thị chính xác mã lỗi `Lỗi hệ thống (500)` lên Toast.
- **Files liên quan**: `frontend/src/pages/EmployeePage.jsx`

### Lỗi MySQL 1406: Data Too Long cho URL Ảnh Đại diện
- **Thời gian**: 2026-05-25 | 19:40:00
- **Vấn đề**: Người dùng copy-paste liên kết ảnh từ Google Search có chứa các tham số redirect dài trên 1000 ký tự vào ô ảnh đại diện, khiến DB MySQL báo lỗi `1406 - Data too long` và Flask trả về lỗi 500.
- **Root cause**: Cột `profile_pic_url` trong schema và model SQLAlchemy được giới hạn kích thước quá ngắn `db.String(500)`.
- **Fix**: Chạy SQL thay đổi cột trên Docker MySQL sang kiểu `MEDIUMTEXT` (hỗ trợ tối đa 16MB) để thoải mái lưu trữ URL dài hoặc Base64. Cập nhật model SQLAlchemy thành `db.Text` để đồng bộ.
- **Files liên quan**: `backend/app/models/employee.py`, *(MySQL database)*

---

## How-To

### Cách Tải File Ảnh và Chuyển Đổi Sang Chuỗi Base64
- **Thời gian**: 2026-05-25 | 19:40:00
- **Bước thực hiện**:
  1. Sử dụng thẻ `<input type="file" accept="image/*" />` để người dùng chọn ảnh từ máy cục bộ.
  2. Bắt sự kiện `onChange` và đọc tệp tin được chọn: `const file = e.target.files[0];`.
  3. Kiểm tra dung lượng tệp tin (ví dụ: giới hạn tối đa `file.size > 2 * 1024 * 1024` cho 2MB).
  4. Sử dụng API trình duyệt `FileReader`: Khởi tạo `const reader = new FileReader();`, đăng ký sự kiện `reader.onloadend` để gán chuỗi kết quả `reader.result` vào state `profile_pic_url` của form dữ liệu.
  5. Kích hoạt đọc file: `reader.readAsDataURL(file)`.
- **Files liên quan**: `frontend/src/pages/EmployeePage.jsx`

### Cách Tải Số Liệu Thống Kê Động Lên Dashboard An Toàn
- **Thời gian**: 2026-05-25 | 19:40:00
- **Bước thực hiện**:
  1. Khai báo state lưu số lượng nhân viên `const [employeeCount, setEmployeeCount] = useState('...');`.
  2. Sử dụng `useEffect` gọi fetch `GET /api/employees` có đính kèm Header Authorization.
  3. Khi nhận danh sách trả về, gán giá trị độ dài danh sách `String(data.length)` vào state.
  4. Truyền giá trị động này vào mảng cấu hình widgets hiển thị trên giao diện Dashboard.
- **Files liên quan**: `frontend/src/pages/DashboardPage.jsx`

### Cách Tạo Sidebar Thu Gọn / Trượt Ra Mượt Mà Cho Desktop & Mobile
- **Thời gian**: 2026-05-28 | 04:15:00
- **Bước thực hiện**:
  1. Khởi tạo state `isSidebarOpen` bằng biểu thức kiểm tra màn hình: `window.innerWidth > 768` (mở mặc định trên Desktop, đóng trên Mobile).
  2. Truyền hàm toggle và đóng từ parent component vào Header & Sidebar.
  3. Cập nhật `App.jsx` để truyền class `app__workspace--shifted` động khi `isSidebarOpen` là `true`.
  4. Trong `Sidebar.jsx`, dùng helper `handleLinkClick` chỉ kích hoạt `onCloseSidebar()` khi ở Mobile (`window.innerWidth <= 768`), giữ sidebar Desktop cố định khi chuyển trang.
  5. Thiết lập CSS base: `.sidebar { transform: translateX(-100%); transition: var(--transition-normal); }` và `.sidebar--open { transform: translateX(0); }`.
  6. Thiết lập CSS cho workspace: `.app__workspace { margin-left: 0; transition: var(--transition-normal); }` và `.app__workspace--shifted { margin-left: var(--sidebar-width); }`. Đảm bảo reset margin về `0 !important` trong media query mobile.
- **Files liên quan**: `frontend/src/App.jsx`, `frontend/src/components/Sidebar.jsx`, `frontend/src/assets/css/index.css`

---

## Patterns

### CSS BEM và Custom Properties trong Thiết Kế Premium Layout
- **Thời gian**: 2026-05-25 | 19:40:00
- **Chi tiết**: Tổ chức toàn bộ CSS hệ thống trong một stylesheet thống nhất, sử dụng triệt để quy ước đặt tên BEM (`.block__element--modifier`) như `.login-card__title`, `.table--zebra`. Mọi màu sắc chủ đạo, bo góc, bóng mờ và thời gian chuyển động được định nghĩa thông qua các biến `:root` giúp việc quản lý, tùy chỉnh giao diện và duy trì tính nhất quán cực kỳ cao.
- **Files liên quan**: `frontend/src/assets/css/index.css`
