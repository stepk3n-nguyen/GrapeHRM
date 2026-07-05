# GrapeHRM — Tiến độ & Lộ trình phát triển

Tài liệu tổng hợp **mọi thứ đã xây dựng** (theo từng giai đoạn) và **lộ trình tiếp theo** của hệ
thống quản lý nhân sự đa tổ chức GrapeHRM.

> Stack: **Flask + SQLAlchemy + MySQL** (backend) · **React 19 + Vite** (frontend) · JWT · multi-tenant.
> Xem [README.md](README.md) để cài đặt nhanh, [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md) để dùng & test theo vai trò.

---

## A. TỔNG QUAN TRẠNG THÁI

| Giai đoạn | Nội dung | Trạng thái |
|-----------|----------|:----------:|
| **P1** | Nền tảng: xác thực, phân quyền, multi-tenant, đổi mật khẩu, cấu hình hệ thống | ✅ Xong |
| **Phase A** | Chấm công GPS / geofence | ✅ Xong |
| **P2** | Báo cáo & Dashboard (biểu đồ) | ✅ Xong |
| **P3** | Tiền lương & phiếu lương PDF | ✅ Xong |
| **P4** | Audit log, Super Admin, SMTP per-tenant, đăng ký tổ chức | ✅ Xong |
| **Phase B** | Lịch ngày lễ theo từng công ty | ✅ Xong |
| **Phase C** | Chiều sâu lương: Thuế TNCN + Tăng ca | ✅ Xong |
| **Phase D** | Refactor xoay quanh Attendance: tổng công tháng tự tính, ca theo nhân viên, về sớm/nửa công tự nhận diện, dashboard chấm công | ✅ Xong |
| **Phase E** | Trợ lý HR AI (Claude) | ⏳ Kế hoạch |

> Kiểm thử: `backend/test_full_flow.py` — **50+ test API end-to-end, tất cả PASS**.
> Dữ liệu demo: `db/grapehrm_full.sql` (restore 1 lệnh: `mysql -u root -p < db/grapehrm_full.sql`) hoặc `backend/seed_demo.py`.

---

## B. ĐÃ HOÀN THÀNH (chi tiết theo giai đoạn)

### P1 — Nền tảng & multi-tenant
- **Kiến trúc đa tổ chức**: mọi bảng có `tenant_id`; middleware `tenant_filter` lấy tenant từ JWT gắn vào `g.tenant_id`; mọi truy vấn cách ly theo công ty.
- **Xác thực & phân quyền**: JWT (access + refresh), 4 vai trò Super Admin / Admin / HR Manager / Nhân viên. Đăng nhập bắt buộc **mã tổ chức** (slug) → tránh trùng username giữa các công ty.
- **Đổi mật khẩu** có kiểm tra độ mạnh; **trang Hệ thống & Bảo mật** (thông tin tổ chức + quản lý người dùng).
- Nhân sự: hồ sơ nhân viên, phòng ban, chức vụ, tài khoản đăng nhập gắn với nhân viên.

### Phase A — Chấm công GPS (geofence)
- Model `WorkLocation` (lat/lng/bán kính) + `WorkShift` (giờ ca, ngưỡng đi muộn, nghỉ trưa).
- Nhân viên **tự check-in/out** bằng GPS trình duyệt; backend kiểm tra khoảng cách tới địa điểm gần nhất bằng **công thức Haversine** (`services/geo.py`); ngoài bán kính → từ chối.
- Tự nhận diện **đi muộn** theo ca; tính giờ công = (ra − vào) − nghỉ trưa.
- Cột geofence trong bảng `attendance`: `check_in_lat/lng`, `check_in_distance_m`, `is_within_geofence`, `source` (SELF/MANUAL).
- HR vẫn nhập/sửa/xóa chấm công thủ công; sửa hết lỗi nghiệp vụ nghỉ phép (server tự tính số ngày, chặn trùng/vượt quỹ, vá rò rỉ phân quyền).

### P2 — Báo cáo & Dashboard
- Blueprint `reports`: `dashboard-stats`, báo cáo nhân sự / nghỉ phép / chấm công + xuất CSV.
- Frontend dùng **recharts** (Line / Bar / Pie / Area); Dashboard lấy số liệu thật.

### P3 — Tiền lương
- 7 model lương (`compensation.py`): cấu trúc lương, phụ cấp, khấu trừ, mức lương nhân viên, đợt lương, phiếu lương, dòng phiếu.
- `payroll_service`: ngày công chuẩn = ngày làm việc thực trong tháng; `lương theo ngày công + phụ cấp − khấu trừ`.
- Đợt lương DRAFT → CONFIRMED → LOCKED; xuất **phiếu lương PDF** (reportlab).

### P4 — Nâng cao
- **Audit log** (`audit_service`) gắn vào đăng nhập / duyệt phép / chạy lương → tab "Nhật ký".
- **Super Admin** quản lý tổ chức (tạo/khóa/mở) + **đăng ký tổ chức công khai**.
- **SMTP per-tenant** mã hóa bằng Fernet (`crypto_service`); email_service ưu tiên cấu hình tenant.

### Phase B — Lịch ngày lễ (theo từng công ty)
- Model `Holiday` (per-tenant, `date` unique theo tenant, `is_paid`, `is_recurring`) + API `/api/holidays` (CRUD + "Nạp lễ VN").
- `services/calendar_service.py`: đếm ngày làm việc **loại T7/CN + ngày lễ**; `services/vn_holidays.py` gom danh mục lễ VN dùng chung.
- **Tích hợp nghiệp vụ**: ngày lễ loại khỏi *ngày công chuẩn* khi tính lương (Tết giảm 5 ngày), và *không trừ quỹ phép* nếu đơn nghỉ trùng lễ.
- **Đa tổ chức**: mỗi công ty có lịch lễ độc lập — theo đúng lịch nhà nước, ít hơn, nhiều hơn, hoặc không có. Công ty mới tự được nạp lịch nhà nước năm hiện tại làm điểm xuất phát.
- Tự sinh chấm công `ON_LEAVE` khi duyệt phép (bỏ T7/CN + lễ) và gỡ khi từ chối đơn đã duyệt.
- UI: tab "Ngày lễ" trong trang Cấu hình chấm công.

### Phase C — Chiều sâu tính lương (Thuế TNCN + Tăng ca)
- **Thuế TNCN** (`services/tax_service.py`): biểu lũy tiến 7 bậc theo tháng, giảm trừ bản thân 11.000.000đ + mỗi người phụ thuộc 4.400.000đ (cột `Employee.num_dependents`).
- **Tăng ca** (`OvertimeRequest`): nhân viên đăng ký → HR duyệt → tự cộng tiền OT theo hệ số luật LĐ (ngày thường 150%, cuối tuần 200%, lễ 300%). API `/api/overtime`, trang **Tăng ca** mới.
- Công thức lương mới: `gross = lương theo ngày công + phụ cấp + OT` → `net = gross − BH bắt buộc − thuế TNCN`. Phiếu lương (UI + PDF) hiển thị đầy đủ gross → thu nhập chịu thuế → thuế → thực lĩnh.

---

## C. LỘ TRÌNH TIẾP THEO

### Đã LOẠI khỏi MVP (quyết định 07/2026)
Ba module dưới đây từng được xây ở mức demo nhưng **không đủ dữ liệu để vận hành thực tế**
với doanh nghiệp vừa và nhỏ tại VN, nên đã gỡ toàn bộ (code + bảng DB) để giữ sản phẩm gọn:

1. **Hợp đồng lao động** — không có mẫu HĐ, không sinh PDF, không đính kèm file, không version,
   không ký số → chỉ là bảng ghi ngày tháng, HR vẫn phải quản lý HĐ giấy song song.
2. **Tuyển dụng** — không upload CV, không lịch phỏng vấn; SME VN tuyển qua Zalo/email là chính.
3. **Đánh giá hiệu suất** — tiêu chí gõ tay tự do, không mục tiêu/kỳ chuẩn → không tạo giá trị.

Khi nào cần, xây lại từng module ở mức dùng được thật (HĐ: mẫu + PDF + lưu file ký scan).

### Phase E — Trợ lý HR AI (Claude) *(điểm nhấn công nghệ — làm cuối)*
- Chatbot dùng **Claude API** trả lời nhân viên/HR bằng tiếng Việt: "Tôi còn bao nhiêu ngày phép?", "Chính sách nghỉ thai sản thế nào?", "Lương tháng này tính ra sao?".
- Kỹ thuật: **function-calling** để truy vấn dữ liệu thật (số dư phép, phiếu lương, chấm công) + **RAG** trên chính sách công ty. Cách ly theo tenant & quyền của người hỏi.
- Làm sau cùng để AI có thể truy vấn toàn bộ dữ liệu các module đã xây.
- *Cần cấu hình API key Anthropic khi triển khai.*

### Đã cân nhắc, chưa làm
- **Phân tích & dự báo** (BI: dự báo nghỉ việc, phát hiện bất thường chấm công) — để dành nếu cần mở rộng thêm.

---

## D. CẤU TRÚC & VẬN HÀNH

```
GrapeHRM/
├── backend/
│   ├── app/
│   │   ├── models/        # tenant, user, employee, leave, work, compensation, holiday...
│   │   ├── <blueprints>/  # auth, employee, leave, admin, reports, compensation, holiday, super_admin, tenant
│   │   ├── services/      # payroll, tax, calendar, vn_holidays, geo, crypto, audit, email, tenant
│   │   └── middleware/    # tenant_filter
│   ├── seed_demo.py       # tạo dữ liệu demo (5 NV, chấm công, OT, lương)
│   └── test_full_flow.py  # 50+ test API end-to-end
├── frontend/src/pages/    # các trang React
├── db/grapehrm_full.sql   # schema + demo (restore 1 lệnh); kèm migration tham khảo
├── README.md              # giới thiệu & cài đặt
├── HUONG_DAN_SU_DUNG.md   # hướng dẫn dùng & kịch bản test theo vai trò
└── TIEN_DO_DU_AN.md       # (file này) tiến độ & lộ trình
```

**Chạy nhanh**
```bash
mysql -u root -p < db/grapehrm_full.sql        # nạp DB + dữ liệu demo
cd backend && pip install -r requirements.txt && python run.py     # :5000
cd frontend && npm install && npm run dev                          # :5173
```

**Tài khoản demo** (mã tổ chức `grapecorp`)

| Tài khoản | Mật khẩu | Vai trò |
|-----------|----------|---------|
| `admin` | `admin123` | Admin |
| `superadmin` | `super123` | Super Admin |
| `an.nv` | `Employee@123` | HR Manager (2 người phụ thuộc) |
| `binh.tt`, `cuong.lv`, `dung.pt`, `em.hv` | `Employee@123` | Nhân viên |

---

## E. ĐIỂM NHẤN CHO ĐỒ ÁN

- **Kiến trúc đa tổ chức (multi-tenant)** cách ly dữ liệu hoàn chỉnh, kể cả lịch nghỉ lễ riêng từng công ty.
- **Chấm công GPS/geofence** bằng Haversine — khác biệt so với HRM CRUD thông thường.
- **Tính lương sát luật Việt Nam**: ngày công chuẩn trừ lễ, tăng ca theo hệ số, **thuế TNCN lũy tiến + giảm trừ gia cảnh**.
- **Trợ lý HR AI** (Phase E) — đóng góp công nghệ nổi bật, tích hợp LLM truy vấn dữ liệu doanh nghiệp.
