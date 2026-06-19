# GrapeHRM — Hướng dẫn sử dụng & Kịch bản test

Tài liệu mô phỏng hành trình **một công ty mới bắt đầu dùng GrapeHRM**: admin thiết lập gì,
nhân viên thao tác ra sao, HR duyệt phép và chạy lương thế nào. Phần cuối là **kịch bản test
end-to-end** có sẵn dữ liệu mẫu để bạn kiểm tra từng tính năng.

---

## 0. Vai trò trong hệ thống

| Vai trò | Quyền chính | Menu thấy được |
|---------|-------------|----------------|
| **Super Admin** | Quản lý nhiều tổ chức (tenant), khóa/mở công ty | Quản lý Tổ chức + mọi menu |
| **Admin** | Toàn quyền trong 1 công ty: cấu hình, nhân sự, lương, hệ thống | Tất cả (trừ Quản lý Tổ chức) |
| **HR Manager** | Nhân sự, duyệt phép, chạy lương, báo cáo | Như admin nhưng **không** có Email/Hệ thống |
| **Nhân viên** | Hồ sơ cá nhân, chấm công GPS, nộp phép, xem phiếu lương | Cá nhân, Nghỉ phép, Chấm công, Phiếu lương |

> Khi đăng nhập đều cần **Mã tổ chức** (slug). Công ty demo có mã `grapecorp`.

---

## 1. Khởi động hệ thống (chạy 1 lần)

```bash
# 1) Tạo & nạp dữ liệu (file SQL duy nhất, đã có sẵn 5 nhân viên demo)
mysql -u root -p < db/grapehrm_full.sql

# 2) Backend (cần MySQL đang chạy)
cd backend
pip install -r requirements.txt
python run.py                       # http://localhost:5000

# 3) Frontend (cửa sổ terminal khác)
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

Mở trình duyệt vào **http://localhost:5173**.

> Muốn bắt đầu **trắng** (công ty thật, không có data demo): bỏ qua bước nạp SQL, chỉ cần
> `CREATE DATABASE grapehrm;` rồi `python run.py` — hệ thống tự tạo bảng và tài khoản admin mặc định.

---

## 2. PHẦN A — Admin thiết lập công ty mới

Đăng nhập: mã `grapecorp` · `admin` · `admin123`. Thứ tự thiết lập khuyến nghị:

### A1. Thông tin tổ chức
**Menu: Hệ thống & Bảo mật → tab Thông tin tổ chức**
Điền tên công ty, mã số thuế, điện thoại, địa chỉ. Đây là thông tin hiển thị trên phiếu lương.

### A2. Cơ cấu tổ chức (phòng ban + chức vụ)
**Menu: Quản lý nhân viên** → nút **"Quản lý Phòng ban"** và **"Quản lý Chức vụ"**
- Tạo phòng ban: vd *Phòng Công nghệ*, *Phòng Kinh doanh*.
- Tạo chức vụ: vd *Trưởng phòng*, *Lập trình viên*, *Nhân viên kinh doanh*.

### A3. Cấu hình chấm công
**Menu: Cấu hình chấm công** (3 tab):
- **Địa điểm làm việc** → "Thêm địa điểm" → bấm **"Lấy vị trí hiện tại"** ngay tại văn phòng để
  lấy đúng toạ độ → đặt bán kính (vd 300m). Nhân viên chỉ chấm công được khi đứng trong vùng này.
- **Ca làm việc** → giờ vào/ra, ngưỡng đi muộn (vd 8:30–17:30, trễ tối đa 15 phút). Đặt 1 ca **mặc định**.
- **Ngày lễ** → lịch nghỉ lễ là **của riêng công ty bạn**. Khi tạo công ty mới, hệ thống nạp
  sẵn lịch nhà nước năm hiện tại làm điểm xuất phát — bạn có thể giữ nguyên, **thêm** ngày nghỉ
  riêng (vd ngày thành lập công ty), **bớt** ngày không nghỉ, hoặc **xóa hết** nếu không áp dụng.
  Bấm **"Nạp lễ VN"** để lấy lại lịch nhà nước cho một năm bất kỳ.
  *Ngày lễ được loại khỏi ngày công chuẩn khi tính lương và không bị trừ quỹ phép.*

  > Lưu ý đa tổ chức: mỗi công ty có lịch lễ độc lập — sửa lịch công ty này không ảnh hưởng công ty khác.
  > Tết/Giỗ tổ theo lịch âm: nút "Nạp lễ VN" chỉ có sẵn cho các năm đã tra cứu (vd 2026); năm khác
  > chỉ nạp lễ dương lịch, bạn tự thêm Tết theo lịch âm năm đó.

### A4. Chính sách nghỉ phép
**Menu: Chính sách phép**
Hệ thống có sẵn 6 loại phép (phép năm, ốm, thai sản, không lương, cưới, tang). Chính sách mặc định
cấp 12 ngày phép năm. Có thể sửa số ngày từng loại và gán chính sách cho nhân viên.

### A5. Cấu hình lương
**Menu: Cấu hình lương** (4 tab):
- **Cấu trúc lương**: mức lương cơ bản theo vị trí (vd Trưởng phòng 20tr, Lập trình viên 15tr).
- **Phụ cấp**: cố định (ăn trưa 730k) hoặc theo % lương.
- **Khấu trừ**: BHXH 8%, BHYT 1.5%, BHTN 1% (theo % lương cơ bản).
- **Gán lương**: chọn nhân viên → gán mức lương + ngày hiệu lực.

### A6. Tạo nhân viên + tài khoản
**Menu: Quản lý nhân viên → "Thêm nhân viên"**
Điền hồ sơ (họ tên, phòng ban, chức vụ, ngày vào làm...). Hệ thống tự sinh mã NV (NV-001...).
Sau đó tạo **tài khoản đăng nhập** cho nhân viên với vai trò tương ứng.

> Thứ tự đúng: A2 (phòng ban/chức vụ) → A5 (cấu trúc lương) → A6 (nhân viên) → gán lương ở A5 tab cuối.

---

## 3. PHẦN B — Nhân viên dùng hằng ngày

Đăng nhập: mã `grapecorp` · `binh.tt` · `Employee@123`.

### B1. Đổi mật khẩu
**Thông tin cá nhân → mục Đổi mật khẩu** (có thanh đo độ mạnh, yêu cầu ≥8 ký tự, chữ hoa/thường/số).

### B2. Chấm công GPS
**Menu: Chấm công** → **"Chấm công vào"** → trình duyệt hỏi quyền vị trí → **Cho phép**.
- Trong bán kính: báo thành công + khoảng cách, tự đánh dấu **đi muộn** nếu quá giờ.
- Ngoài bán kính: bị từ chối kèm thông báo *"cách Xm, cho phép 300m"*.
- Cuối ngày bấm **"Chấm công ra"** → hệ thống tính giờ công (trừ giờ nghỉ trưa).

> ⚠ GPS trình duyệt chỉ hoạt động ở **localhost** hoặc **HTTPS**. Mở từ điện thoại qua
> `http://192.168.x.x:5173` sẽ bị trình duyệt chặn lấy vị trí.

### B3. Nộp đơn nghỉ phép
**Menu: Nghỉ phép → "Tạo đơn"** → chọn loại phép, ngày bắt đầu/kết thúc, lý do.
- Hệ thống tự tính số ngày (loại T7/CN + ngày lễ), kiểm tra **không vượt quỹ** và **không trùng** đơn khác.
- Xem **số dư phép** còn lại của từng loại.

### B4. Xem phiếu lương
**Menu: Phiếu lương** → chọn tháng/năm → xem chi tiết (lương cơ bản theo ngày công, phụ cấp +,
khấu trừ −, thực lĩnh) → **Tải PDF**. *Chỉ xem được khi HR đã chạy & xác nhận bảng lương.*

---

## 4. PHẦN C — HR / Quản lý

Đăng nhập: mã `grapecorp` · `an.nv` · `Employee@123` (vai trò HR Manager).

### C1. Duyệt nghỉ phép
**Menu: Nghỉ phép** → đơn ở trạng thái *Chờ duyệt* → **Duyệt** hoặc **Từ chối** (kèm lý do).
- Khi duyệt: hệ thống **tự tạo bản ghi chấm công ON_LEAVE** cho các ngày nghỉ (bỏ T7/CN + lễ),
  và gửi email thông báo cho nhân viên.
- Khi từ chối đơn đã duyệt: tự gỡ các ngày ON_LEAVE đã tạo.

### C2. Báo cáo
**Menu: Báo cáo** (3 tab có biểu đồ): Nhân sự (theo phòng ban, giới tính, độ tuổi),
Nghỉ phép (theo loại, theo tháng, top người nghỉ), Chấm công (đúng giờ/muộn/vắng). Có xuất CSV.

### C3. Chạy bảng lương
**Menu: Bảng lương → "Chạy lương"** → chọn tháng/năm.
1. Hệ thống tính cho từng NV: `thực lĩnh = lương cơ bản × (ngày công + phép có lương)/ngày công chuẩn + phụ cấp − khấu trừ`.
2. Trạng thái **Nháp** → kiểm tra → **Xác nhận** → **Khóa**.
3. Sau khi xác nhận, nhân viên mới xem được phiếu lương. Bấm **Tải PDF** từng phiếu.

---

## 5. PHẦN D — Kịch bản test end-to-end

Dùng dữ liệu mẫu có sẵn để kiểm chứng từng luồng. ✅ = kết quả mong đợi.

### Test 1 — Phân quyền đăng nhập
| Bước | Kết quả mong đợi |
|------|------------------|
| Đăng nhập `admin`/`admin123` | ✅ Thấy Dashboard + đầy đủ menu cấu hình |
| Đăng nhập `binh.tt`/`Employee@123` | ✅ Chỉ thấy Cá nhân, Nghỉ phép, Chấm công, Phiếu lương |
| Đăng nhập sai mã tổ chức | ✅ Báo lỗi, không vào được |

### Test 2 — Chấm công GPS (cần làm tại văn phòng)
1. Admin: Cấu hình chấm công → Địa điểm → "Lấy vị trí hiện tại" → lưu (bán kính 300m).
2. Nhân viên: Chấm công → "Chấm công vào" → Cho phép GPS.
   - ✅ Đứng tại văn phòng → thành công, hiện khoảng cách.
   - ✅ Tạm đặt bán kính 10m rồi thử lại → bị từ chối "ngoài phạm vi".

### Test 3 — Nghỉ phép → duyệt → tự sinh chấm công
1. `binh.tt` nộp đơn phép năm 3 ngày (chọn ngày thường, không trùng đơn cũ).
   - ✅ Số ngày tự tính, trừ vào số dư phép.
2. `an.nv` (HR) vào Nghỉ phép → Duyệt đơn đó.
   - ✅ Đơn chuyển *Đã duyệt*; vào Chấm công của `binh.tt` thấy các ngày đó là **ON_LEAVE**.
3. Thử nộp đơn trùng ngày → ✅ bị chặn "trùng với đơn khác".
4. Thử nộp đơn vượt số ngày phép còn lại → ✅ bị chặn "vượt quỹ phép".

### Test 4 — Ngày lễ ảnh hưởng nghiệp vụ
1. Admin: Cấu hình chấm công → Ngày lễ → "Nạp lễ VN" (năm 2026).
   - ✅ Thêm 10 ngày lễ (Tết, 30/4, 1/5, 2/9...).
2. Nhân viên nộp đơn nghỉ bao trùm 30/4–1/5.
   - ✅ Số ngày trừ quỹ **không tính** 30/4 và 1/5 (vì là ngày lễ).
3. Khi chạy lương tháng có lễ → ✅ "ngày công chuẩn" giảm tương ứng (Tết tháng 2 giảm 5 ngày).

### Test 5 — Bảng lương + phiếu lương
> Dữ liệu mẫu **đã có sẵn bảng lương tháng 5/2026 (đã xác nhận)**. Để xem ngay: Bảng lương →
> mở đợt T5/2026. Để test chạy mới: chọn **tháng 6/2026** (cũng có chấm công sẵn).
1. `admin` hoặc `an.nv`: Bảng lương → mở đợt **T5/2026** (hoặc Chạy lương **T6/2026**).
   - ✅ 5 phiếu, mỗi phiếu hiện ngày công / ngày chuẩn, phụ cấp, khấu trừ, thực lĩnh.
   - vd Trần Thị Bình: cơ bản 15tr → thực lĩnh ~14.455.000đ.
2. Xác nhận đợt lương → Tải PDF 1 phiếu → ✅ ra file PDF.
3. Đăng nhập `binh.tt` → Phiếu lương → tháng 5/2026 → ✅ xem được phiếu của mình + tải PDF.

### Test 6 — Báo cáo & Dashboard
1. `admin` → Dashboard → ✅ thấy tổng nhân sự, tỷ lệ chấm công, biểu đồ phòng ban.
2. Báo cáo → 3 tab → ✅ biểu đồ nhân sự / nghỉ phép / chấm công hiển thị đúng số liệu.

### Test 7 — Super Admin
1. Đăng nhập `superadmin`/`super123` → ✅ thấy menu "Quản lý Tổ chức".
2. Tạo tổ chức mới → ✅ tạo kèm tài khoản admin riêng cho tổ chức đó.
3. Khóa/mở 1 tổ chức → ✅ tổ chức bị khóa không đăng nhập được.

---

## 6. Phụ lục — Tài khoản & lệnh nhanh

**Tài khoản demo** (mã tổ chức: `grapecorp`)

| Tài khoản | Mật khẩu | Vai trò |
|-----------|----------|---------|
| `admin` | `admin123` | Admin |
| `superadmin` | `super123` | Super Admin |
| `an.nv` | `Employee@123` | HR Manager (Phòng CN) |
| `binh.tt` · `cuong.lv` | `Employee@123` | Nhân viên (Phòng CN) |
| `dung.pt` · `em.hv` | `Employee@123` | Nhân viên (Kinh doanh) |

**Lệnh nhanh**
```bash
mysql -u root -p < db/grapehrm_full.sql   # nạp lại dữ liệu mẫu bất cứ lúc nào
cd backend && python run.py                # backend  :5000
cd frontend && npm run dev                 # frontend :5173
cd backend && python test_full_flow.py     # tự test 43+ API (backend phải đang chạy)
cd backend && python seed_demo.py          # tạo lại dữ liệu mẫu (nếu dùng DB trắng)
```
