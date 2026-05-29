# Báo cáo thực chiến: Xử lý cột STT và chuẩn hóa ID Nhân viên

Xin chào! Nay mình ngồi lại bàn chút về task vừa rồi nhé. Nhìn có vẻ đơn giản là "thêm cột số thứ tự (STT)" và "format lại mã NV", nhưng thực ra có kha khá thứ thú vị đằng sau đấy.

---

### Phần 1: Approach & Reasoning
Ban đầu khi bạn bảo "thêm cột STT", mình cứ nghĩ theo hướng "bài bản" nhất của backend: thêm một cột vào Database, cho nó giá trị mặc định, rồi API trả dữ liệu xuống. Mình làm vậy vì nghĩ rằng STT nên được cố định với từng nhân sự từ lúc sinh ra. Nhưng thực tế, STT trên giao diện chỉ là công cụ để admin dễ nhìn đếm dòng thôi. Việc nhồi một biến thiên thuần túy UI xuống Database là over-engineering (làm quá vấn đề). Rút cục là chuyển hướng, tính STT ngay trên React (bằng `index + 1`).

Còn vụ format lại "NV-XXX", hệ thống code Python hiện tại đã tự sinh mã 3 chữ số rất chuẩn rồi. Vấn đề chỉ nằm ở các dữ liệu "đời đầu" (bị lưu thành NV-01, NV-02...). Thế nên mình quyết định không đụng vào code mà viết một câu lệnh SQL Update chọc thẳng vào Database để sửa chữa (sử dụng LPAD và SUBSTRING). Nhanh, gọn, lẹ.

### Phần 2: Roads Not Taken
Con đường bị "fail" rõ nhất: Mình từng thử thêm field `serial` thẳng vào SQLAlchemy Model `Employee`. Mình nghĩ cứ khai báo default=0 là xong. Sai bét! Khi bạn khai báo model nhưng chưa chạy migration (`alembic upgrade` hoặc `ALTER TABLE`), SQLAlchemy tự tin ném cái cột `serial` vào truy vấn `SELECT serial, ... FROM employees`. Thế là MySQL vỗ mặt: "Unknown column 'serial'". Do đó, con đường thay đổi Schema Database bị từ bỏ vì nó không đáng để đổi lấy một tính năng UI cỏn con.

### Phần 3: How Things Connect
Bạn hãy tưởng tượng flow như thế này: Database -> SQLAlchemy -> Flask API -> React UI.
STT (Số thứ tự) là thứ chỉ có ý nghĩa ở "chặng cuối" (React UI) khi bạn muốn show lên màn hình hoặc in ra giấy. Việc nhét STT vào tận "chặng đầu" (Database) giống như việc dán nhãn số ghế vào thẳng vé máy bay ngay khi khách mới vào phòng chờ mua vé, trong khi khách có thể đổi trả, thêm bớt. Tốt nhất là lúc nào xếp hàng lên máy bay (Render UI), mới đếm `1, 2, 3`.

### Phần 4: Tools & Methods
Thay vì viết một script Python loop qua từng bản ghi để format "NV-01" thành "NV-001", mình dùng thuần MySQL command:
`UPDATE employees SET employee_id = CONCAT('NV-', LPAD(SUBSTRING(employee_id, 4), 3, '0'))`
Lý do: SQL sinh ra để thao tác tập hợp. Các hàm xử lý chuỗi của MySQL (LPAD, SUBSTRING) giải quyết gọn trong 1 phần nghìn giây và 1 dòng lệnh. Không tốn effort tạo migration hay script, không lo out of memory.

### Phần 5: Tradeoffs
- **Thêm cột ở UI**: Đánh đổi một xíu (rất nhỏ) CPU của trình duyệt khi chạy `.map((emp, index) => ...)`, đổi lại là backend sạch sẽ, Database nhẹ gánh, không cần quản lý việc đánh lại số khi có nhân viên nghỉ việc (xóa bản ghi).
- **Update Database trực tiếp**: Đánh đổi việc "không có dấu vết trong code history" lấy sự tiện lợi và tốc độ nhanh. (Nhưng bù lại chúng ta có file learning này lưu lại dấu vết đó).

### Phần 6: Mistakes & Dead Ends
Ngõ cụt đau nhất là cái màn "Cứ tưởng thêm trong model là được". Bạn biết đó, khi làm việc với ORM như SQLAlchemy, thay đổi Model trong code Python KHÔNG có nghĩa là bảng trong MySQL sẽ tự động thay đổi theo. Việc mình cứ cố `db.session.add()` trong khi bảng ở dưới chưa có cột mới đã sinh ra lỗi 500 "Không thể tải danh sách nhân viên". Bài học rút ra: ORM là một tấm gương phản chiếu Database, nó không phải là cái khuôn ép Database phải đổi theo.

### Phần 7: Future Pitfalls
Cạm bẫy cực lớn cho những task "thêm field": Hãy tự hỏi "Field này thuộc về domain logic (Nghiệp vụ) hay presentation logic (Giao diện)".
- Nếu là Nghiệp vụ (ví dụ: cấp bậc nhân sự): Phải lưu Database.
- Nếu là Giao diện (STT, màu sắc hiển thị): Hãy giữ nó ở Frontend. 
Đừng vội vã tạo cột trong Database.

### Phần 8: Expert vs Beginner
- **Beginner**: Nhận yêu cầu thêm STT -> Thêm biến `stt` vào Entity backend -> Viết API trả ra -> Lên giao diện map. Thấy sai sai khi xóa 1 người thì bị khuyết số (1, 2, 4). Lại viết API để update lại toàn bộ `stt` của những người đằng sau. Rất cồng kềnh!
- **Expert**: Nhận yêu cầu thêm STT -> `<td>{index + 1}</td>` ở Frontend. Tốn 5 giây.

### Phần 9: Transferable Lessons
- **Phân tách trách nhiệm (Separation of Concerns)**: UI chỉ nên lo việc render. Backend lo data.
- **SQL is King**: Khi làm việc với Data cleansing (Dọn dẹp dữ liệu cũ), hãy nhớ đến sức mạnh của các hàm SQL (như LPAD, RPAD, SUBSTRING). Việc thao tác trực tiếp trên DB thường an toàn và nhanh hơn rất nhiều so với việc tải lên RAM qua Python rồi đẩy xuống.
