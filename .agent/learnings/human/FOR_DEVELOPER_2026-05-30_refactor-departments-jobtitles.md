# Giải Phẫu: Refactor Chức vụ, Thêm Phòng ban & Computed State

Yo! Vừa làm xong một quả update khá to cho cái màn Quản lý Nhân viên. Chúng ta đã biến cái form 1 cột chật chội thành form 3 cột cực kỳ thoáng, thêm quản lý Phòng ban (Department), đổi tên Vị trí thành Chức vụ (Job Title), và đặc biệt nhất là trò "tự động tính trạng thái" (Computed State) siêu hay. Hãy ngồi xuống uống ngụm cà phê, tớ kể lại toàn bộ quá trình nhé.

## Phần 1: Approach & Reasoning

Ngay từ đầu, yêu cầu đặt ra là khá nhiều: vừa sửa database (thêm bảng, đổi tên cột), vừa sửa logic API (JobPosition thành JobTitle, thêm Department, tính toán lại State), vừa sửa UI (Grid 3 cột, thêm các Select box). 

Tớ bắt đầu từ móng trước: Database. Vì dùng SQL thuần để update (cái này tớ sẽ nói kỹ hơn ở phần "Mistakes"), sau đó là update SQLAlchemy Models để nó match với database. Xong xuôi tớ mới đụng đến API routes. Cuối cùng, khi backend đã trả về đúng format `employee` với đầy đủ `title_name`, `department_name`, `address`... thì tớ mới đập đi xây lại cái giao diện form trên `EmployeePage.jsx`.

## Phần 2: Roads Not Taken

Lúc làm chức năng "Tự động tính Trạng thái công việc (ACTIVE/TERMINATED)", có 2 con đường:
1. **Dùng Cron Job**: Chạy ngầm một tác vụ mỗi đêm lúc 0h, kiểm tra xem ông nào có `end_date <= hôm_nay` thì update database.
2. **Computed State (Trạng thái tính toán động)**: Tính toán thẳng lúc người dùng fetch API.

Tớ đã dứt khoát ném cái trò Cron Job ra chuồng gà. Vì sao? Vì nó quá cồng kềnh cho một ứng dụng nhỏ/vừa. Thêm Cron job là phải thêm thư viện (`Celery` hoặc `APScheduler`), thêm process, và có nguy cơ lỗi ngầm. Thay vào đó, tớ tính toán state mỗi khi serialize trả về API. Vừa nhanh, vừa chính xác realtime 100%. Nếu có thay đổi, tớ ngầm update luôn xuống DB (`db.session.commit()`).

## Phần 3: How Things Connect

Mọi thứ liên kết với nhau theo trục dọc (Vertical Slice):
- Tầng Data: `department_id` + `title_id` + `end_date` nằm dưới DB.
- Tầng Model: SQLAlchemy mapping các relationship `department` và `title` vào Employee.
- Tầng API: Serialize hàm lấy luôn `.name` của hai bảng kia, tiện tay tính toán lại `state`.
- Tầng UI: React fetch data về, render lên bảng (Zebra table) rất nhẹ nhàng vì Backend đã làm hết trò "join" và "tính toán". Form 3 cột trên UI chỉ làm nhiệm vụ hiển thị và gửi đúng các ID xuống.

## Phần 4: Tools & Methods

Tớ dùng `CSS Grid` (`display: grid; grid-template-columns: repeat(3, 1fr)`) thay vì `Flexbox` cho form. Tại sao? Flexbox giỏi trong việc dàn hàng 1 chiều, nhưng để tạo một cái form "ma trận" (matrix) 3 cột đều tăm tắp, Grid là trùm. Nó ép các cột bằng nhau chằn chặn mà không cần phải set `width: 33.33%` thủ công hay lo bị vỡ layout khi nội dung dài ngắn khác nhau.

Về backend, tớ viết SQL thô (`ALTER TABLE`) thông qua `docker exec` thay vì dùng Migration Tools.

## Phần 5: Tradeoffs

Việc tính toán `state` ở thời điểm Serialize API (Computed State) có một tradeoff nhỏ:
- Mất thêm một chút xíu CPU time ở backend mỗi khi gọi GET list nhân viên, vì nó phải chạy vòng lặp check `end_date` so với ngày hôm nay.
Nhưng đổi lại, ta không bao giờ lo dữ liệu bị "out of sync" hay phải maintain một con cron job chập chờn.

## Phần 6: Mistakes & Dead Ends

Hôm qua tớ dính một cú lừa từ `db.create_all()` của SQLAlchemy. Nó chỉ tạo bảng mới chứ không hề update (`ALTER`) các bảng đã có. Tớ cứ đinh ninh đổi tên trong model xong khởi động lại Flask là xong, ai ngờ lúc gọi API báo `Unknown column position_id`. Cuối cùng, tớ nhận ra phải viết script SQL thủ công để `RENAME` bảng, `ADD COLUMN`, và setup khóa ngoại bằng tay. Sự thật mất lòng: SQLAlchemy không thần thánh như ta tưởng nếu không có Alembic đi kèm!

## Phần 7: Future Pitfalls

Hãy cẩn thận với cái trò `ON DELETE SET NULL`. Lúc setup khóa ngoại cho `title_id` và `department_id`, tớ dùng cái này. Nghĩa là nếu xóa một phòng ban, nhân viên thuộc phòng đó sẽ có `department_id = NULL` chứ không bị xóa theo. Cạm bẫy ở đây là trên UI, code của bạn phải luôn check `emp.department_name || 'Không có'` nếu không sẽ dính lỗi Null Pointer Exception khi render!

## Phần 8: Expert vs Beginner

Một beginner sẽ tạo một select box `state` trên UI, bắt người dùng phải chọn "Đang làm" hoặc "Đã nghỉ", mặc dù đã có cái ô "Ngày kết thúc". 
Một expert nhận ra rằng: "Khoan đã, nếu tao biết ngày kết thúc của mày, tao có thể tự suy ra mày còn làm hay không mà?". Đó gọi là nguyên tắc **SSOT (Single Source Of Truth)**. Không bao giờ lưu 2 thông tin có thể suy ra từ nhau để bắt người dùng phải update cả 2.

## Phần 9: Transferable Lessons

1. **Grid cho Forms**: Cứ form nhiều trường, cứ ốp Grid vào. Đừng dùng Flexbox, nó sẽ làm bạn khóc lúc responsive. 
2. **Computed Properties**: Luôn luôn tự hỏi "Trường dữ liệu này có thể suy ra từ các trường khác không?". Nếu có, hãy tính toán nó động, đừng bắt user nhập. Hệ thống thông minh là hệ thống lười biếng bắt user làm ít nhất có thể!

Uống xong ly cà phê rồi đấy, hy vọng cậu thấy phần refactor này thú vị!
