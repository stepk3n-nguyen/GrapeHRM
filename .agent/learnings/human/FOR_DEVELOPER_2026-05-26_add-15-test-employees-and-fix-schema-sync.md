# Cà phê cùng dev: Câu chuyện thêm 15 nhân viên mẫu và cái kết bất ngờ với SQLAlchemy

Chào bạn, ngồi xuống làm ngụm cà phê nhé! Hôm nay chúng ta vừa xử lý xong một yêu cầu tưởng chừng như rất cơ bản: tạo thêm 15 nhân viên mẫu (NV-01 đến NV-15) cho hệ thống GrapeHRM. Nhưng như mọi khi, lập trình không bao giờ dễ dàng như vẻ bề ngoài của nó, và mình đã "đạp mìn" ngay lập tức. Để mình kể bạn nghe quá trình này nhé.

## 1. Approach & Reasoning
Ban đầu, khi nhận yêu cầu thêm 15 nhân viên với định dạng tên và email cụ thể, mình đã chọn cách viết một Python script (`add_15_employees.py`) chạy trực tiếp trong Flask App Context thay vì dùng SQL thuần hay gọi API liên tục. 
Tại sao ư?
- Thứ nhất: Dùng SQLAlchemy model sẽ tận dụng được logic có sẵn (như tự động lấy `tenant_id` và các validations mặc định).
- Thứ hai: Script chạy một lần (one-off) rất dễ kiểm soát, có thể check xem nhân viên đã tồn tại chưa (`Employee.query.filter_by...`) để tránh duplicate nếu lỡ chạy lại.

## 2. Roads Not Taken
Mình đã nghĩ đến việc dùng vòng lặp Bash hoặc dùng Javascript (frontend) gửi 15 POST requests đến API `/employees`. Nhưng mình đã từ bỏ:
- Gọi API 15 lần có vẻ hơi "cục súc" và phụ thuộc vào kết nối mạng/proxy của Docker.
- Dùng SQL thuần (`INSERT INTO...`) thì lại rủi ro nếu có các trường bắt buộc mà mình quên (như `created_at`, `tenant_id`), và phải hardcode các enum.

Do đó, viết script Python dùng ORM là con đường cân bằng nhất giữa "nhanh" và "an toàn".

## 3. How Things Connect
Script này kết nối trực tiếp với Database thông qua `create_app()` của Flask. Khi gọi `app.app_context()`, chúng ta có được kết nối DB và Tenant hiện tại. Sau đó, mỗi lần lặp là một lần khởi tạo object `Employee`, gán các trường random và gọi `db.session.add()`. Cuối cùng `db.session.commit()` một lần duy nhất để lưu lại. Quá trình này mô phỏng y hệt như việc gửi 15 API requests nhưng ở tầng dưới cùng.

## 4. Tools & Methods
Mình sử dụng Python script chạy bằng lệnh `docker exec grapehrm-api-1 python /app/add_15_employees.py`. Phương pháp này cho phép chọc thẳng vào môi trường production-like (containerized) mà không cần cài cắm gì trên máy host. Tất cả thư viện (SQLAlchemy, PyMySQL) đều đã có sẵn.

## 5. Tradeoffs
Quyết định dùng Script có một đánh đổi: nó bypass các validations logic nằm ở tầng View/Controller (ví dụ các hàm kiểm tra ảnh hợp lệ, hay format số điện thoại). Ở đây mình ưu tiên **tốc độ setup data mẫu** nên chấp nhận việc data có thể không qua phễu lọc hoàn hảo của API.

## 6. Mistakes & Dead Ends
Và đây là lúc câu chuyện trở nên thú vị. Khi chạy script lần đầu, nó ném ra một lỗi đỏ chót: `(1054, "Unknown column 'employees.middle_name' in 'field list'")`.
Chuyện gì đã xảy ra?
Trước đó (ở một session khác), chúng ta đã quyết định xóa trường "Tên phụ" (`middle_name`) khỏi giao diện và database. Tuy nhiên, cái bẫy ở đây là: **Cột trong Database đã bị xóa, nhưng thuộc tính `middle_name` trong class `Employee` (SQLAlchemy Model) thì vẫn còn lù lù ra đó!**
Khi SQLAlchemy query DB để kiểm tra xem nhân viên đã tồn tại chưa (`filter_by`), nó tự động tạo ra một câu `SELECT id, first_name, middle_name, last_name...`. Database nhận được câu query và ngớ người: "Ủa, cột middle_name là cột nào?". Kết quả là ứng dụng crash.

Mình đã phải quay lại file `app/models/employee.py`, xóa định nghĩa `middle_name` và sửa luôn hàm `full_name()` để không còn tham chiếu đến thuộc tính ma này nữa. Sau đó chạy lại kịch bản thì thành công mỹ mãn.

## 7. Future Pitfalls
Bài học xương máu: Khi bạn xóa một cột trong database (hoặc đổi tên), **HÃY LUÔN NHỚ CẬP NHẬT ORM MODEL TƯƠNG ỨNG**. Database schema và ORM Model là hai tấm gương phản chiếu lẫn nhau, nếu một bên thay đổi mà bên kia không biết, hệ thống sẽ gãy ngay từ lúc gọi query đơn giản nhất.

## 8. Expert vs Beginner
Một beginner khi gặp lỗi 1054 ("Unknown column") sẽ hoảng hốt đi tìm xem ai đổi tên cột trong SQL, hay cố gắng `ALTER TABLE` thêm lại cột đó vào cho đỡ lỗi.
Một expert sẽ nhận ra ngay "Sự mất đồng bộ giữa Code và Data". Họ hiểu rằng SQLAlchemy biên dịch Model class thành câu SQL, và vấn đề nằm ở việc Model đang đòi một thứ mà DB không còn cung cấp. Họ sẽ bình tĩnh update code để phản ánh đúng hiện thực của DB.

## 9. Transferable Lessons
- **Single Source of Truth là ảo tưởng nếu bạn có ORM**: Code và Schema luôn có nguy cơ lệch nhịp. Việc sử dụng tool migration (như Alembic) sinh ra chính là để đồng bộ hóa quá trình này (code thay đổi -> sinh file migration -> apply vào DB), giúp cả 2 luôn đi song song. Nếu làm thủ công một trong hai, sớm muộn cũng sẽ "vấp cỏ".
- **Lỗi ở quá khứ có thể ám sát bạn ở tương lai**: Việc quên update model ở các task trước đã không gây lỗi ngay (vì không ai query đến nó), cho đến khi mình viết script chạy query lên toàn bộ record. Đừng để lại "nợ kỹ thuật" dù là nhỏ nhất.

Đó là toàn bộ câu chuyện. Giờ thì hệ thống đã có đủ 15 nhân viên mẫu để test, và mã nguồn cũng sạch sẽ hơn một chút rồi! Tách cà phê ngon chứ?
