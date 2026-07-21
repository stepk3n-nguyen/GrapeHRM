# GrapeHRM — Hệ thống Quản lý Nhân sự đa tổ chức (multi-tenant)

Ứng dụng HRM web cho nhiều công ty dùng chung một hệ thống (multi-tenant). Quản lý nhân sự,
chấm công bằng GPS/geofence, nghỉ phép, tính lương và phiếu lương, báo cáo, nhật ký kiểm toán.

> Đồ án tốt nghiệp. Backend Flask + MySQL, Frontend React 19 + Vite.

---

## Tính năng chính

| Nhóm | Chức năng |
|------|-----------|
| **Xác thực & phân quyền** | JWT, 4 vai trò: Super Admin / Admin / HR Manager / Nhân viên. Đăng nhập theo mã tổ chức. |
| **Nhân sự** | Hồ sơ nhân viên, phòng ban, chức vụ, tài khoản đăng nhập. |
| **Chấm công (geofence)** | Nhân viên tự check-in/out bằng GPS trình duyệt; kiểm tra vị trí trong bán kính công ty (Haversine); tự nhận diện **đi muộn / về sớm / nửa công** theo ca làm của TỪNG nhân viên (nhiều ca, gán ca riêng). |
| **Tổng công tháng** | Tự động tính từ dữ liệu chấm công + nghỉ phép + tăng ca (không nhập tay): ngày đủ công, nửa công, thiếu chấm ra, đi muộn, phép, nghỉ không lương, vắng không phép, giờ OT, TỔNG CÔNG. Xuất CSV mở bằng Excel. |
| **Nghỉ phép** | Đơn nghỉ → HR duyệt, quỹ phép theo chính sách, chống trùng/vượt quỹ; duyệt xong TỰ SINH chấm công ON_LEAVE (từ chối thì tự gỡ) — một nguồn dữ liệu duy nhất, không nhập 2 nơi. |
| **Lịch ngày lễ** | Lịch nghỉ lễ **riêng từng công ty**; loại khỏi ngày công chuẩn (lương) và quỹ phép. |
| **Tăng ca (OT)** | Nhân viên đăng ký tăng ca → HR duyệt → tự cộng tiền OT vào lương theo hệ số luật LĐ (thường 150%, cuối tuần 200%, lễ 300%). |
| **Tiền lương** | Cấu trúc lương, phụ cấp/khấu trừ, **thuế TNCN lũy tiến + giảm trừ gia cảnh**, lương gross→net, chạy bảng lương theo ngày công thực tế, phiếu lương PDF. |
| **Báo cáo** | Dashboard xoay quanh chấm công: hôm nay ai đi làm / đi muộn / nghỉ phép / vắng, tỷ lệ đi làm, tổng công + OT tháng hiện tại; báo cáo nhân sự/nghỉ phép/chấm công với biểu đồ, xuất CSV. |
| **Quản trị** | Nhật ký kiểm toán (audit log), cấu hình SMTP per-tenant (mã hóa Fernet), Super Admin quản lý tổ chức. |

---

## Kiến trúc multi-tenant

- **Chia sẻ DB/schema**: mọi bảng nghiệp vụ có cột `tenant_id`. Mỗi truy vấn lọc theo tenant
  hiện tại (lấy từ JWT, gắn vào `g.tenant_id` qua middleware `before_request`).
- **Cách ly dữ liệu**: nhân viên, chấm công, lương, **ngày lễ**... đều là dữ liệu riêng của
  từng công ty — không công ty nào thấy dữ liệu của công ty khác.
- **Ngày lễ theo từng công ty**: vì lịch nghỉ tùy doanh nghiệp, mỗi tenant có lịch lễ riêng,
  có thể theo đúng lịch nhà nước, **ít hơn, nhiều hơn, hoặc không có ngày nào**. Khi tạo công ty
  mới, hệ thống nạp sẵn lịch nhà nước năm hiện tại làm điểm xuất phát; admin tự thêm/bớt/xóa sau.

---

## Công nghệ

- **Backend**: Python, Flask 3.1, SQLAlchemy, Flask-JWT-Extended, Flask-Marshmallow, PyMySQL, reportlab (PDF), cryptography (Fernet).
- **Frontend**: React 19, Vite, React Router v7, lucide-react, recharts.
- **CSDL**: MySQL 8+ (utf8mb4).

---

## Cấu trúc thư mục

```
GrapeHRM/
├── backend/
│   ├── app/
│   │   ├── models/           # SQLAlchemy models (tenant, user, employee, leave, work, compensation, holiday...)
│   │   ├── auth/ employee/ leave/ admin/ reports/ compensation/ holiday/ super_admin/ tenant/   # blueprints
│   │   ├── services/         # payroll_service, calendar_service, vn_holidays, geo, crypto, audit, email, tenant_service
│   │   ├── middleware/        # tenant_filter (gắn g.tenant_id)
│   │   ├── seed.py            # seed tenant + admin + mặc định khi khởi động
│   │   └── __init__.py        # application factory + đăng ký blueprint
│   ├── seed_demo.py           # tạo dữ liệu demo (5 nhân viên, chấm công, lương)
│   ├── test_full_flow.py      # tự test 43+ API end-to-end
│   └── run.py
├── frontend/
│   └── src/pages/             # các trang React (Dashboard, Attendance, Leave, Payroll, WorkConfig...)
├── db/
│   ├── grapehrm_full.sql      # FILE SQL DUY NHẤT: schema + dữ liệu demo (restore 1 lệnh)
│   └── migration_2026_07_attendance_refactor.sql  # Migration tham khảo cho DB cũ
├── README.md
└── HUONG_DAN_SU_DUNG.md       # hướng dẫn sử dụng & kịch bản test chi tiết
```

---

## Cài đặt & chạy

**Yêu cầu**: Python 3.10+, Node.js 18+, MySQL 8+.

```bash
# 1) Cơ sở dữ liệu — cách A: nạp sẵn dữ liệu demo (khuyến nghị để xem ngay)
# Nạp schema + dữ liệu demo bằng 1 lệnh (mật khẩu root MySQL của bạn):
mysql -u root -p < db/grapehrm_full.sql

# (Cách khác: tạo DB trống — schema tự tạo khi chạy backend, demo: python seed_demo.py)
#    cách B: bắt đầu trắng cho công ty thật
#    mysql -u root -p -e "CREATE DATABASE grapehrm CHARACTER SET utf8mb4;"

# 2) Backend
cd backend
pip install -r requirements.txt
python run.py                  # http://localhost:5000  (tự tạo bảng + seed nếu DB trống)

# 3) Frontend (terminal khác)
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

Cấu hình kết nối MySQL ở `backend/app/config.py` (mặc định `root:12312312@localhost:3306/grapehrm`)
hoặc qua biến môi trường `DATABASE_URL`.

---

## Tài khoản demo

Mã tổ chức: **`grapecorp`**

| Tài khoản | Mật khẩu | Vai trò |
|-----------|----------|---------|
| `admin` | `admin123` | Admin |
| `superadmin` | `super123` | Super Admin |
| `an.nv` | `Employee@123` | HR Manager |
| `binh.tt`, `cuong.lv`, `dung.pt`, `em.hv` | `Employee@123` | Nhân viên |

---

## Kiểm thử

```bash
cd backend && python test_full_flow.py     # 43+ test API (backend phải đang chạy)
```

Xem **[HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md)** để có hướng dẫn sử dụng theo vai trò
và kịch bản test end-to-end từng tính năng.

---

## Lưu ý chấm công GPS

`navigator.geolocation` của trình duyệt chỉ hoạt động ở **secure context** (HTTPS hoặc `localhost`).
Mở app từ điện thoại qua `http://<địa-chỉ-IP>:5173` sẽ bị trình duyệt chặn lấy vị trí — cần HTTPS
(ví dụ ngrok) hoặc test trực tiếp trên laptop tại `localhost`.
