<h1> GrapeHRM — Hệ thống Quản lý Nhân sự đa tổ chức (multi-tenant) </h1>

Ứng dụng HRM web cho nhiều công ty dùng chung một hệ thống (multi-tenant). Quản lý nhân sự,                                                                                                                                                                                                     
chấm công bằng GPS/geofence, nghỉ phép, tính lương và phiếu lương, báo cáo, nhật ký kiểm toán.

> Đồ án tốt nghiệp. Backend Flask + MySQL, Frontend React 19 + Vite.

---

## Tính năng chính

| Nhóm | Chức năng |
|------|-----------|
| **Xác thực & phân quyền** | JWT (access + refresh token), 4 vai trò: Super Admin / Admin / HR Manager / Nhân viên. Đăng nhập theo mã tổ chức (slug). |
| **Nhân sự** | Hồ sơ nhân viên, phòng ban, chức vụ, tài khoản đăng nhập, trang hồ sơ cá nhân. |
| **Chấm công (geofence)** | Nhân viên tự check-in/out bằng GPS trình duyệt; kiểm tra vị trí trong bán kính công ty (Haversine); tự nhận diện **đi muộn / về sớm / nửa công** theo ca làm của TỪNG nhân viên (nhiều ca, gán ca riêng). |
| **Cấu hình ca & địa điểm** | Quản lý ca làm việc (work shift), địa điểm làm việc (work location) với tọa độ GPS + bán kính geofence. |
| **Tổng công tháng** | Tự động tính từ dữ liệu chấm công + nghỉ phép + tăng ca (không nhập tay): ngày đủ công, nửa công, thiếu chấm ra, đi muộn, phép, nghỉ không lương, vắng không phép, giờ OT, TỔNG CÔNG. Xuất CSV mở bằng Excel. |
| **Nghỉ phép** | Đơn nghỉ → HR duyệt, quỹ phép theo chính sách, chống trùng/vượt quỹ; duyệt xong TỰ SINH chấm công ON_LEAVE (từ chối thì tự gỡ) — một nguồn dữ liệu duy nhất. |
| **Chính sách phép** | Cấu hình loại phép (annual, sick, maternity…), chính sách phép theo loại nhân viên, quỹ phép tự trừ theo lịch lễ. |
| **Lịch ngày lễ** | Lịch nghỉ lễ **riêng từng công ty**; loại khỏi ngày công chuẩn (lương) và quỹ phép. Khi tạo công ty mới, hệ thống nạp sẵn lịch nhà nước VN năm hiện tại. |
| **Tăng ca (OT)** | Nhân viên đăng ký tăng ca → HR duyệt → tự cộng tiền OT vào lương theo hệ số luật LĐ (thường 150%, cuối tuần 200%, lễ 300%). |
| **Tiền lương** | Cấu trúc lương, phụ cấp/khấu trừ, **thuế TNCN lũy tiến + giảm trừ gia cảnh**, lương gross→net, chạy bảng lương theo ngày công thực tế, phiếu lương PDF (reportlab). |
| **Báo cáo** | Dashboard: hôm nay ai đi làm / đi muộn / nghỉ phép / vắng, tỷ lệ đi làm, tổng công + OT tháng hiện tại; báo cáo nhân sự/nghỉ phép/chấm công với biểu đồ (recharts), xuất CSV. |
| **Email thông báo** | Gửi email khi duyệt/từ chối nghỉ phép, tăng ca, v.v. Cấu hình SMTP riêng từng tenant (mã hóa Fernet). |
| **Quản trị** | Nhật ký kiểm toán (audit log), cấu hình hệ thống, Super Admin quản lý tổ chức (CRUD tenant). |

---

## Kiến trúc multi-tenant

- **Chia sẻ DB/schema**: mọi bảng nghiệp vụ có cột `tenant_id`. Mỗi truy vấn lọc theo tenant
  hiện tại (lấy từ JWT, gắn vào `g.tenant_id` qua middleware `before_request`).
- **Cách ly dữ liệu**: nhân viên, chấm công, lương, ngày lễ... đều là dữ liệu riêng của
  từng công ty — không công ty nào thấy dữ liệu của công ty khác.
- **Ngày lễ theo từng công ty**: mỗi tenant có lịch lễ riêng, có thể theo đúng lịch nhà nước,
  ít hơn, nhiều hơn, hoặc không có ngày nào. Khi tạo công ty mới, hệ thống nạp sẵn lịch
  nhà nước năm hiện tại làm điểm xuất phát; admin tự thêm/bớt/xóa sau.

---

## Công nghệ

| Lớp | Stack |
|-----|-------|
| **Backend** | Python 3.10+, Flask 3.1, SQLAlchemy, Flask-Migrate (Alembic), Flask-JWT-Extended, Flask-Marshmallow, Flask-CORS, PyMySQL, bcrypt, reportlab (PDF), cryptography (Fernet), python-dotenv, gunicorn |
| **Frontend** | React 19, Vite 8, React Router v7, lucide-react (icons), recharts (biểu đồ) |
| **CSDL** | MySQL 8+ (utf8mb4) |

---

## Cấu trúc thư mục

```
GrapeHRM/
├── backend/
│   ├── app/
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── tenant.py          # Tenant (tổ chức)
│   │   │   ├── user.py            # User (tài khoản đăng nhập)
│   │   │   ├── employee.py        # Employee (hồ sơ nhân viên)
│   │   │   ├── attendance.py      # Attendance (chấm công)
│   │   │   ├── leave.py           # LeaveType, LeavePolicy, LeaveRequest, LeaveBalance
│   │   │   ├── work.py            # WorkLocation, WorkShift (ca & địa điểm)
│   │   │   ├── compensation.py    # SalaryStructure, Allowance, Deduction, Payroll, PayrollItem
│   │   │   ├── holiday.py         # Holiday (ngày lễ)
│   │   │   ├── audit_log.py       # AuditLog (nhật ký kiểm toán)
│   │   │   ├── email_log.py       # EmailLog
│   │   │   ├── tenant_config.py   # TenantConfig (SMTP per-tenant)
│   │   │   └── base.py            # TenantMixin
│   │   ├── auth/              # Blueprint: đăng nhập, đổi mật khẩu, refresh token
│   │   ├── employee/          # Blueprint: CRUD nhân viên, phòng ban, chức vụ
│   │   ├── attendance/        # Blueprint: chấm công, ca làm, địa điểm
│   │   ├── leave/             # Blueprint: loại phép, chính sách phép, đơn nghỉ, quỹ phép
│   │   ├── compensation/      # Blueprint: cấu trúc lương, payroll, phiếu lương
│   │   ├── holiday/           # Blueprint: lịch ngày lễ
│   │   ├── reports/           # Blueprint: báo cáo & dashboard API
│   │   ├── admin/             # Blueprint: audit log, cấu hình admin
│   │   ├── tenant/            # Blueprint: thông tin tenant hiện tại
│   │   ├── super_admin/       # Blueprint: CRUD tenant (Super Admin)
│   │   ├── services/          # Business logic layer
│   │   │   ├── attendance_service.py   # Tính tổng công tháng
│   │   │   ├── payroll_service.py      # Chạy bảng lương
│   │   │   ├── tax_service.py          # Thuế TNCN lũy tiến VN
│   │   │   ├── payslip_pdf.py          # Xuất phiếu lương PDF
│   │   │   ├── calendar_service.py     # Tính ngày công chuẩn (trừ lễ + weekend)
│   │   │   ├── vn_holidays.py          # Seed lịch nghỉ lễ Việt Nam
│   │   │   ├── geo.py                  # Haversine check GPS
│   │   │   ├── crypto_service.py       # Fernet encrypt/decrypt (SMTP password)
│   │   │   ├── audit_service.py        # Ghi audit log
│   │   │   ├── email_service.py        # Gửi email thông báo
│   │   │   ├── email_templates.py      # Template HTML email
│   │   │   ├── tenant_service.py       # Tạo tenant + seed defaults
│   │   │   └── schema_upgrade.py       # Auto-upgrade schema cho DB cũ
│   │   ├── middleware/
│   │   │   └── tenant_filter.py   # Gắn g.tenant_id từ JWT vào mỗi request
│   │   ├── assets/fonts/          # Font cho reportlab (phiếu lương PDF)
│   │   ├── config.py              # Config theo môi trường (dev/prod/test)
│   │   ├── extensions.py          # db, migrate, jwt, cors, ma
│   │   ├── seed.py                # Seed tenant mặc định + tài khoản admin/superadmin
│   │   └── __init__.py            # Application factory (create_app)
│   ├── seed_demo.py               # Tạo dữ liệu demo (nhân viên, chấm công, lương)
│   ├── .env.example               # Mẫu biến môi trường
│   ├── requirements.txt
│   └── run.py                     # Entry point: python run.py → localhost:5000
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx          # Đăng nhập (chọn mã tổ chức)
│   │   │   ├── DashboardPage.jsx      # Tổng quan hôm nay
│   │   │   ├── EmployeePage.jsx       # Quản lý nhân viên
│   │   │   ├── ProfilePage.jsx        # Hồ sơ cá nhân
│   │   │   ├── AttendancePage.jsx     # Chấm công + tổng công tháng
│   │   │   ├── WorkConfigPage.jsx     # Cấu hình ca & địa điểm
│   │   │   ├── LeavePage.jsx          # Đơn nghỉ phép
│   │   │   ├── LeavePolicyPage.jsx    # Chính sách phép
│   │   │   ├── OvertimePage.jsx       # Đăng ký & duyệt tăng ca
│   │   │   ├── SalaryConfigPage.jsx   # Cấu hình cấu trúc lương
│   │   │   ├── PayrollPage.jsx        # Chạy bảng lương & phiếu lương
│   │   │   ├── MyPayslipPage.jsx      # Nhân viên xem phiếu lương của mình
│   │   │   ├── ReportsPage.jsx        # Báo cáo biểu đồ
│   │   │   ├── SettingsPage.jsx       # Cài đặt hệ thống (lịch lễ, audit log)
│   │   │   ├── EmailSettingsPage.jsx  # Cấu hình SMTP tenant
│   │   │   └── SuperAdminPage.jsx     # Quản lý tổ chức (Super Admin)
│   │   ├── components/
│   │   │   ├── Header.jsx         # Thanh header
│   │   │   ├── Sidebar.jsx        # Sidebar điều hướng (theo vai trò)
│   │   │   └── Footer.jsx         # Footer
│   │   ├── context/
│   │   │   └── AuthContext.jsx    # Context xác thực (JWT, vai trò, tenant)
│   │   ├── utils/
│   │   │   └── authFetch.js       # Fetch wrapper: auto-attach token, refresh khi hết hạn
│   │   ├── App.jsx                # Router chính + layout
│   │   ├── main.jsx               # Entry point React
│   │   └── index.css              # CSS toàn cục
│   ├── index.html
│   ├── vite.config.js             # Vite config: port 3000, proxy /api → :5000
│   └── package.json
├── db/
│   ├── grapehrm_full.sql          # FILE SQL DUY NHẤT: schema + dữ liệu demo (restore 1 lệnh)
│   └── migration_2026_07_attendance_refactor.sql  # Migration tham khảo cho DB cũ
├── README.md
├── HUONG_DAN_SU_DUNG.md           # Hướng dẫn sử dụng & kịch bản test chi tiết
├── TIEN_DO_DU_AN.md               # Tiến độ dự án
└── descriptions.md                # Mô tả tổng quan quy trình HRM
```

---

## Cài đặt & chạy

**Yêu cầu**: Python 3.10+, Node.js 18+, MySQL 8+.

### 1. Cơ sở dữ liệu

**Cách A — Nạp sẵn dữ liệu demo (khuyến nghị để xem ngay):**

```bash
mysql -u root -p < db/grapehrm_full.sql
```

**Cách B — Bắt đầu trắng cho công ty thật:**

```bash
mysql -u root -p -e "CREATE DATABASE grapehrm CHARACTER SET utf8mb4;"
# Schema sẽ tự tạo khi chạy backend lần đầu.
# Muốn có dữ liệu demo: cd backend && python seed_demo.py
```

### 2. Backend

```bash
cd backend

# Tạo file .env từ mẫu, sửa mật khẩu MySQL
copy .env.example .env        # Windows
# cp .env.example .env        # Linux/macOS

# Cài dependencies
pip install -r requirements.txt

# Chạy server
python run.py                  # http://localhost:5000
```

> Khi chạy lần đầu, backend tự động: tạo bảng (`db.create_all`) → nâng cấp schema (`schema_upgrade`) → seed tenant mặc định + tài khoản admin/superadmin.

### 3. Frontend (terminal khác)

```bash
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

> Vite đã cấu hình proxy: mọi request `/api/*` từ frontend tự chuyển tới `http://localhost:5000` — không cần lo CORS khi dev.

### Cấu hình kết nối MySQL

Sửa file `backend/.env` (hoặc biến môi trường `DATABASE_URL`):

```
DATABASE_URL=mysql+pymysql://root:MAT_KHAU_MYSQL@localhost:3306/grapehrm
```

Mặc định (nếu không có `.env`): `root:12312312@localhost:3306/grapehrm`.

---

## Tài khoản demo

Mã tổ chức: **`grapecorp`**

| Tài khoản | Mật khẩu | Vai trò |
|-----------|----------|---------|
| `superadmin` | `super123` | Super Admin |
| `admin` | `admin123` | Admin |
| `an.nv` | `Employee@123` | HR Manager |
| `binh.tt`, `cuong.lv`, `dung.pt`, `em.hv` | `Employee@123` | Nhân viên |

> Tài khoản `superadmin` và `admin` được tự tạo bởi `seed.py` khi DB trống.
> Các nhân viên demo được tạo bởi `seed_demo.py` hoặc import từ `db/grapehrm_full.sql`.

---

## Biến môi trường

Xem file [`backend/.env.example`](backend/.env.example) để biết danh sách đầy đủ:

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `FLASK_ENV` | Môi trường (`development` / `production`) | `development` |
| `DATABASE_URL` | Chuỗi kết nối MySQL | `mysql+pymysql://root:12312312@localhost:3306/grapehrm` |
| `JWT_SECRET_KEY` | Khóa bí mật JWT | `change-me-in-production` |
| `ENCRYPTION_KEY` | Khóa Fernet (mã hóa SMTP password) | _(tự sinh nếu trống)_ |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | Email gửi | _(trống)_ |
| `MAIL_PASSWORD` | App password email | _(trống)_ |

---

## Lưu ý chấm công GPS

`navigator.geolocation` của trình duyệt chỉ hoạt động ở **secure context** (HTTPS hoặc `localhost`).
Mở app từ điện thoại qua `http://<địa-chỉ-IP>:3000` sẽ bị trình duyệt chặn lấy vị trí — cần HTTPS
(ví dụ ngrok) hoặc test trực tiếp trên laptop tại `localhost`.

---

## Tài liệu bổ sung

- [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md) — Hướng dẫn sử dụng theo vai trò & kịch bản test end-to-end
- [TIEN_DO_DU_AN.md](TIEN_DO_DU_AN.md) — Tiến độ phát triển dự án
- [descriptions.md](descriptions.md) — Mô tả tổng quan quy trình HRM & flowchart
