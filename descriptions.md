> **Mô tả tổng quan**
> GrapeHRM cung cấp một chuỗi quy trình nhân sự (HR) tích hợp, hỗ trợ từ tuyển dụng đến nghỉ hưu. Dưới đây là workflow chính được tổ chức thành các mô-đun:

## 1. Tuyển dụng (Recruitment)
1. **Tạo vị trí công việc** – Định nghĩa mô tả, yêu cầu và phòng ban.
2. **Thu thập hồ sơ** – Ứng viên nộp CV qua form tuyển dụng.
3. **Phỏng vấn** – Lịch biểu, ghi chú, đánh giá.
4. **Ra quyết định** – Cấp đề nghị, gửi thư mời qua email.
5. **Ký hợp đồng** – Tạo hợp đồng trong hệ thống, lưu trữ.

## 2. Onboarding (Đón nhận nhân viên mới)
- Tạo tài khoản người dùng trong GrapeHRM.
- Giao nhiệm vụ, cấp quyền truy cập.
- Thiết lập hồ sơ cá nhân.

## 3. Quản lý nhân viên (Employee Management)
- Hồ sơ cá nhân: thông tin cá nhân, hợp đồng, bằng cấp.
- Thay đổi thông tin: vị trí, trạng thái, mức lương, thông tin liên hệ,...
- Theo dõi thâm niên, ngày sinh, ngày nghỉ.

## 4. Quản lý thời gian & Nghỉ phép (Time & Leave)
1. **Yêu cầu nghỉ** – Nhân viên nộp đơn nghỉ, chọn loại (annual, sick, maternity…).
2. **Phê duyệt** – Quản lý xem xét, phê duyệt hoặc từ chối.
3. **Cập nhật cân bằng** – Hệ thống tự tính toán ngày còn lại.
4. **Báo cáo** – Tổng hợp ngày nghỉ, xuất file CSV/PDF.

## 5. Đánh giá hiệu suất (Performance Management)
- **Mục tiêu**: Đặt KPI, mục tiêu cá nhân/đội.
- **Đánh giá định kỳ**: Tự đánh giá → Đánh giá bởi cấp trên.
- **Kết quả**: Xác định tăng lương, khen thưởng, kế hoạch phát triển.

## 6. Quản lý tiền lương (Compensation)
- Cấu hình bảng lương, phụ cấp, phụ thu.
- Tự động tính lương dựa trên thời gian làm việc, nghỉ phép.
- In/Export bảng lương.

## 7. Thông tin báo cáo (Reporting)
- Báo cáo nhân sự (tổng số nhân viên, tỷ lệ nghỉ).
- Báo cáo tuyển dụng (thời gian tuyển, nguồn ứng viên).
- Báo cáo hiệu suất, chi phí nhân sự.

---

## Mermaid Flowchart – Tổng quan quy trình HRM
```mermaid
flowchart TD
    A[Khởi tạo vị trí tuyển dụng] --> B[Đăng tuyển & thu thập hồ sơ]
    B --> C[Sàng lọc & phỏng vấn]
    C --> D[Ra quyết định & ký hợp đồng]
    D --> E[Onboarding nhân viên mới]
    E --> F[Quản lý nhân viên] --> G[Quản lý thời gian & nghỉ phép]
    F --> H[Đánh giá hiệu suất] --> I[Quản lý tiền lương]
    I --> J[Báo cáo & phân tích]
```
---

### Lưu ý triển khai
- **Cấu hình ban đầu**: Thiết lập các role (Admin, HR Manager, Supervisor, Employee).
- **Tích hợp**: Kết nối với LDAP/Active Directory nếu cần.
- **Kiểm thử**: Thực hiện test quy trình từ tuyển dụng tới trả lương.
- **Đào tạo người dùng**: Hướng dẫn HR và các manager sử dụng các module.