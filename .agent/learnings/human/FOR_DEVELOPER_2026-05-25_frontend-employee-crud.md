# Chia sẻ về hành trình xây dựng Frontend & Employee CRUD cho GrapeHRM
*Chào người bạn đồng hành! Ngồi xuống làm ly cà phê ☕️ rồi cùng tôi nhìn lại hành trình lập trình vừa qua nhé. Dưới đây là những chia sẻ chi tiết và thực tế nhất về cách tôi xây dựng hệ thống này, những gì đã học được, cả những lỗi "dở khóc dở cười" mà chúng ta đã cùng nhau vượt qua.*

---

## 1. Cách tiếp cận & Logic suy nghĩ (Approach & Reasoning)
Khi bắt đầu task này, mục tiêu của tôi là tạo ra một bộ mặt **Vite React** cực kỳ xịn sò và một hệ thống **Employee CRUD API** thực sự chạy được ở phía Flask Backend. 

Điểm xuất phát của tôi là: **Quy tắc thiết kế cốt lõi (Web Design Backbone Rule)**. Đây không chỉ là một tài liệu quy định, nó là triết lý thiết kế. Một trang quản trị nhân sự cao cấp thì không thể có giao diện "phẳng lì, nhạt nhẽo" (flat & plain). 
Tôi đã quyết định thiết lập một hệ thống CSS variables chặt chẽ và áp dụng chuẩn BEM (`block__element--modifier`) ngay từ đầu để viết CSS thuần (Vanilla CSS) mượt mà nhất. 

Về kiến trúc xử lý ảnh đại diện, tôi chọn cách chuyển đổi tệp tin sang chuỗi **Base64 Data URL** ngay ở Client-side. Cách này giúp đơn giản hóa cực kỳ nhiều cho Backend: không cần tạo thư mục static lưu ảnh, không lo phân quyền ghi file trên đĩa cứng Docker, và dữ liệu ảnh tự động được lưu cô lập theo dòng dữ liệu của từng doanh nghiệp (multi-tenant) trong MySQL.

---

## 2. Những ngã rẽ không chọn (Roads Not Taken)
Trong quá trình làm, có 3 con đường lớn tôi đã cân nhắc nhưng quyết định **bỏ qua**:

- **Không dùng Tailwind CSS:** Mặc dù Tailwind rất tiện, nhưng quy tắc cốt lõi của dự án yêu cầu Vanilla CSS nguyên bản để có sự kiểm soát tuyệt đối về mặt mỹ thuật và hiệu ứng mượt mà. Việc viết CSS thuần theo chuẩn BEM giúp mã nguồn giao diện sạch sẽ, dễ đọc hơn rất nhiều so với một đống class hỗn độn trong HTML.
- **Không dùng Multipart Form-Data để upload ảnh:** Cách làm truyền thống là dùng `FormData` gửi file nhị phân lên Backend. Nhưng cách này sẽ bắt chúng ta phải viết thêm một Controller upload riêng ở Flask, cấu hình đường dẫn tĩnh, lo lắng về CORS, và quản lý việc xóa ảnh cũ trên ổ đĩa. Base64 hóa ảnh giúp payload gọn gàng chỉ trong một request JSON duy nhất.
- **Không dùng Local/Mocked Data cho CRUD:** Tôi hoàn toàn có thể giả lập dữ liệu trên Frontend để hoàn thành nhanh task. Nhưng tôi chọn viết hẳn REST API thực tế trên Flask Backend. Một giao diện đẹp mà bấm nút không lưu được gì vào database thì chỉ là một cái vỏ rỗng. Việc kết nối thực tế giúp chúng ta phát hiện ra những vấn đề cốt lõi về kiểu dữ liệu (như lỗi quá độ dài cột MySQL bên dưới).

---

## 3. Các mảnh ghép khớp với nhau như thế nào? (How Things Connect)
Hãy tưởng tượng hệ thống của chúng ta hoạt động như một chuỗi bánh răng khớp nối:
```text
[Trình duyệt] ──(Token trong LocalStorage)──> [AuthContext] ──(Authorization Header)──> [Flask Middleware]
     │                                                                                        │
[Giao diện] <──(Lọc dữ liệu mượt mà) <── [Zebra Table / Modal Form] <── (Lọc g.tenant_id) <── [Database]
```

- **AuthContext** là trái tim bảo mật. Nó quản lý token đăng nhập và tự động cung cấp Header `Authorization: Bearer <token>` cho mọi request API khác.
- Khi người dùng đăng nhập thành công, token được lưu. Giao diện chính kích hoạt, kết hợp **Header cố định** phía trên, **Sidebar** điều hướng bên trái và vùng **Workspace** ở giữa.
- Khi truy cập trang *Quản lý nhân viên*, table thực hiện fetch danh sách. Khi người dùng bấm *Thêm mới*, Modal scale-up hiện ra. Khi bấm nút *Lưu*, ảnh đại diện được chuyển thành Base64, lồng vào payload JSON gửi lên API và lưu trực tiếp xuống MySQL. Tất cả diễn ra đồng bộ, trơn tru.

---

## 4. Công cụ & Phương pháp (Tools & Methods)
Tôi đã lựa chọn các công cụ và thư viện rất chọn lọc:
- **Vite:** Công cụ build cực nhanh, hỗ trợ Hot Module Replacement (HMR) giúp thay đổi code giao diện hiển thị ngay lập tức trên trình duyệt.
- **Lucide React:** Bộ icon SVG sắc nét, nhẹ nhàng và hiện đại, giúp giao diện trông cực kỳ premium thay vì dùng các icon thô hay các thư viện nặng nề.
- **FileReader API:** Phương thức chuyển đổi ảnh sang Base64 chuẩn của trình duyệt, hiệu năng tốt và cực kỳ ổn định.
- **Vite API Proxy:** Cấu hình chuyển hướng `/api` trong `vite.config.js` giúp tránh được hoàn toàn rào cản CORS trong quá trình phát triển cục bộ.

---

## 5. Đánh đổi (Tradeoffs)
Quyết định kiến trúc nào cũng có sự đánh đổi:
- **Base64 Encoding vs Dung lượng Database:** Sử dụng Base64 giúp việc upload ảnh siêu đơn giản, nhưng bù lại, dung lượng của chuỗi Base64 sẽ lớn hơn file nhị phân khoảng 33%. Điều này làm tăng kích thước bản ghi trong MySQL và dung lượng JSON truyền tải qua mạng. 
- Để cân bằng, tôi đã thêm cơ chế **validate giới hạn file tối đa 2MB** ở Frontend để chặn các file ảnh quá lớn gây quá tải đường truyền và phình to database.

---

## 6. Sai lầm & Những ngõ cụt (Mistakes & Dead Ends)
Chúng ta đã cùng nhau trải qua một lỗi rất kinh điển: **"Không thể kết nối đến máy chủ"** khi bấm lưu nhân viên mới.
Quá trình debug lỗi này như một câu chuyện trinh thám:

- Lúc đầu, thông báo lỗi *"Không thể kết nối..."* làm ta tưởng mạng Docker bị đứt. 
- Nhưng khi tôi kiểm tra `docker logs grapehrm-api-1`, tôi phát hiện ra lỗi thực tế bên dưới là **`sqlalchemy.exc.DataError: (1406, "Data too long for column 'profile_pic_url'")`**. Do người dùng copy một URL ảnh chuyển hướng dài tới hơn 900 ký tự từ Google, trong khi cột DB chỉ cho phép 500.
- Điểm "ngõ cụt" tiếp theo là tại sao lỗi DB lại biến thành lỗi mất mạng trên giao diện? À! Là do Frontend mặc định gọi `await response.json()` mà không kiểm tra xem server có trả về HTML báo lỗi 500 hay không. Việc parse JSON trên một trang HTML lỗi ném ra exception và đẩy luồng code vào catch block tổng!
- **Bài học khắc phục:** Tôi đã sửa lại Frontend để kiểm tra Content-Type trước khi parse JSON, đồng thời chạy SQL trực tiếp nâng cấp cột MySQL lên `MEDIUMTEXT` (16MB) để giải quyết triệt để lỗi độ dài ảnh.

---

## 7. Cạm bẫy trong tương lai (Future Pitfalls)
Khi bạn tiếp tục phát triển dự án này, hãy lưu ý:
- **Độ trễ đồng bộ file trên Windows (WSL2):** Do Docker chạy trên môi trường ảo hóa WSL2 của Windows, thỉnh thoảng các sự kiện thay đổi file ở máy thật không được Linux phát hiện kịp thời để reload Vite. Nếu thấy code không đổi, hãy chạy `docker restart grapehrm-frontend-1` như tôi đã làm.
- **Kích thước ảnh Base64 phình to:** Trong tương lai nếu có hàng nghìn nhân sự, bạn nên cân nhắc viết thêm module nén/resize ảnh trên Frontend (dùng canvas) trước khi convert sang Base64 để tối ưu hóa triệt để hiệu năng lưu trữ của Database.

---

## 8. Góc nhìn Chuyên gia (Expert vs Beginner)
- **Beginner** thường sẽ hoảng loạn khi thấy lỗi "Không thể kết nối máy chủ", cố gắng restart lại Docker vô ích hoặc hardcode rút ngắn URL ảnh một cách thủ công. Họ cũng thường cấu hình CORS ở Backend một cách lỏng lẻo (`origins: "*"`) thay vì dùng Proxy phát triển của Vite.
- **Expert** sẽ bình tĩnh mở logs của container để truy vết lỗi SQL thực tế, nhận ra lỗ hổng của cơ chế parse JSON khi server trả về mã 500, và nâng cấp cột dữ liệu lên `MEDIUMTEXT` kết hợp với file size validation ở client để chặn đứng các nguy cơ lỗi dữ liệu trong tương lai.

---

## 9. Bài học có thể tái sử dụng (Transferable Lessons)
Bài học lớn nhất từ dự án này là: **Đừng bao giờ tin tưởng tuyệt đối vào định dạng phản hồi từ API**. Luôn kiểm tra `Content-Type` hoặc bọc việc parse JSON trong `try-catch` trước khi xử lý. 

Ngoài ra, việc đóng gói toàn bộ kiểu dáng giao diện thông qua hệ thống **CSS Variables** kết hợp chuẩn **BEM** là một vũ khí cực mạnh giúp bạn có thể dễ dàng chuyển đổi Dark/Light mode hay tái cấu hình màu sắc thương hiệu chỉ trong vòng 5 giây!

*Hy vọng những chia sẻ "bên ly cà phê" này giúp bạn hiểu sâu sắc hơn về hệ thống chúng ta vừa cùng nhau xây dựng. Chúc bạn luôn tràn đầy cảm hứng sáng tạo trên hành trình lập trình của mình!* 🚀
