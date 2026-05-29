# Sidebar Thu Gọn & Trượt Nhịp Nhàng (Collapsible Sidebar Toggle)

> Chia sẻ nhỏ từ ly cà phê buổi sáng về cách chúng ta "hô biến" cái thanh sidebar tĩnh thành một hệ thống trượt mở cực kỳ mượt mà và sang xịn mịn cho cả máy tính lẫn điện thoại.
> Cập nhật lần cuối: 2026-05-28 | 04:20:00

---

## 1. Tiếp cận & Tư duy thiết kế (Approach & Reasoning)

Khi nhận yêu cầu *"muốn slide bar bên trái có thể thụt vào và trượt ra khi ấn nút toggle"*, mục tiêu của mình không chỉ đơn giản là làm cho nó biến mất rồi hiện lại. Mình muốn tạo ra một trải nghiệm **"premium"** thực sự – nghĩa là khi sidebar trượt đi, phần nội dung chính (workspace) cũng phải giãn nở ra một cách êm ái, tạo cảm giác toàn bộ bố cục đang thở và chuyển dịch đồng bộ.

**Điểm bắt đầu:**
Chúng ta có `App.jsx` quản lý state mở/đóng `isSidebarOpen`. Tuy nhiên, trước đây state này chỉ phục vụ cho mobile drawer. Trên desktop, sidebar luôn chễm chệ chiếm 250px và workspace luôn thụt lề (`margin-left: 250px`).
Ý tưởng cốt lõi ở đây là:
1. Đồng bộ hóa state `isSidebarOpen` cho cả Desktop và Mobile.
2. Dùng CSS Class động trên Workspace (`app__workspace--shifted`) để điều khiển margin.
3. Đồng bộ hóa thời gian chuyển động (transition duration) giữa Sidebar và Workspace để chúng dịch chuyển nhịp nhàng cùng lúc.

---

## 2. Những con đường không chọn (Roads Not Taken)

*   **Cách 1: Thay đổi trực tiếp style qua inline CSS (`style={{ marginLeft: isSidebarOpen ? 250 : 0 }}`)**
    *   *Tại sao bỏ:* Inline style ép trình duyệt phải re-evaluate CSS liên tục, phá vỡ tính phân tách của cấu trúc BEM CSS. Quan trọng hơn, viết thế này sẽ khó tùy biến hơn khi viết Media Queries (ví dụ: trên mobile ta muốn cưỡng chế margin về 0 bất kể sidebar đóng hay mở).
*   **Cách 2: Dùng `position: absolute` cho Workspace trên Desktop**
    *   *Tại sao bỏ:* Nếu workspace tuyệt đối hóa, khi sidebar hiện ra nó sẽ đè lên trên nội dung chính thay vì đẩy nội dung sang bên. Trải nghiệm này trên màn hình rộng trông rất chật chội và kém chuyên nghiệp. Nội dung bị che mất một góc là điều tối kỵ trong thiết kế UX.

---

## 3. Các mảnh ghép khớp với nhau như thế nào? (How Things Connect)

Hệ thống hoạt động như một chuỗi Domino tinh tế:
1.  **Nguồn kích hoạt (Trigger):** Nút Hamburger ở `Header.jsx` gọi `onToggleSidebar` truyền ngược lên `App.jsx`.
2.  **Bộ não (State Manager):** `App.jsx` thay đổi `isSidebarOpen` từ `true` sang `false` (hoặc ngược lại).
3.  **Hành động đồng bộ (Execution):**
    *   `<Sidebar>` nhận `isOpen`, thêm class `.sidebar--open` -> Trình duyệt chạy hiệu ứng dịch chuyển phần cứng `transform: translateX(...)`.
    *   `<main>` nhận class `.app__workspace--shifted` -> Thay đổi `margin-left` từ `0` thành `250px`.
    *   Cả hai đều chia sẻ chung biến transition `--transition-normal: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)` nên tốc độ trượt và tốc độ nở của khung hình khớp nhau hoàn hảo đến từng mili-giây!

---

## 4. Công cụ & Phương pháp (Tools & Methods)

*   **Khởi tạo State Động (Dynamic Initial State):**
    ```javascript
    const [isSidebarOpen, setIsSidebarOpen] = useState(() => 
      typeof window !== 'undefined' ? window.innerWidth > 768 : false
    );
    ```
    *Tại sao lại là callback này?* Nó giúp website thông minh ngay từ giây đầu tiên tải trang. Nếu mở bằng PC, sidebar tự động bung ra sẵn sàng làm việc. Nếu mở bằng Smartphone, sidebar tự ẩn đi để nhường chỗ cho nội dung chính, tránh tình trạng giật lag hay nhấp nháy UI khi khởi động.

---

## 5. Đánh đổi (Tradeoffs)

*   **Hy sinh một chút hiệu năng Reflow lấy Trải nghiệm Premium:**
    Thay đổi `margin-left` của Workspace sẽ kích hoạt tiến trình *Reflow/Layout* của trình duyệt (trình duyệt phải tính toán lại kích thước hiển thị của toàn bộ thẻ con bên trong). Nếu dùng `transform` cho cả workspace thì hiệu năng sẽ cao hơn (chỉ chạy ở Composite layer của GPU).
    *Tuy nhiên*, nếu dùng `transform` cho workspace, phần nội dung bên phải màn hình sẽ bị đẩy ra ngoài rìa viewport (mất một khoảng hiển thị). Vì vậy, mình chấp nhận đánh đổi một lượng rất nhỏ tài nguyên CPU/GPU để đổi lại một layout giãn nở tự nhiên, các bảng số liệu tự co giãn vừa vặn với kích thước màn hình mới.

---

## 6. Góc khuất & Những lần gỡ lỗi (Mistakes & Dead Ends)

**Cạm bẫy "Tự Động Đóng" trên Desktop:**
Khi tích hợp xong, mình phát hiện ra một bug rất ngớ ngẩn: Trên desktop, cứ mỗi lần click chọn một menu (ví dụ: chuyển từ Dashboard sang Quản lý nhân viên), sidebar tự động thụt vào mất tiêu!
*Nguyên nhân:* Trước đó trên Mobile, để tiện lợi thì khi người dùng click link, hệ thống sẽ kích hoạt `onCloseSidebar()` để đóng drawer. Đoạn code cũ trong `Sidebar.jsx` viết:
`onClick={onCloseSidebar}` cho thẻ `NavLink`.
*Cách xử lý:* Mình đã viết lại một helper cực kỳ đáng yêu:
```javascript
const handleLinkClick = () => {
  if (window.innerWidth <= 768) {
    onCloseSidebar();
  }
};
```
Giờ đây, sidebar chỉ tự đóng khi ở màn hình nhỏ (mobile), còn trên PC nó sẽ kiên định đứng vững bất chấp bạn có click chuyển trang bao nhiêu lần đi nữa!

---

## 7. Cạm bẫy tương lai cần tránh (Future Pitfalls)

*   **Resizing đột ngột:** Biểu thức `window.innerWidth > 768` chỉ chạy **duy nhất một lần** khi mount component. Nếu người dùng quay ngang màn hình tablet hay resize trình duyệt liên tục giữa chừng, state sẽ không tự động đồng bộ lại. Nhưng bạn yên tâm, họ vẫn có thể bấm nút Toggle thủ công để điều chỉnh. Nếu sau này thực sự cần, ta có thể lắng nghe thêm sự kiện `resize` toàn cục.
*   **Mobile Reset:** Luôn nhớ giữ quy tắc `!important` cho margin trên Mobile trong CSS Media Query để đề phòng trường hợp class `--shifted` của Desktop vô tình bị giữ lại làm vỡ layout màn hình nhỏ.

---

## 8. Tư duy Expert vs Beginner (Expert vs Beginner)

*   **Beginner:** Sẽ viết các state riêng biệt cho Desktop và Mobile, hoặc viết JS đo đạc pixel thủ công rồi gán trực tiếp. Kết quả là code rối nùi, chuyển động giật cục và rất khó bảo trì.
*   **Expert:** Giữ React State cực kỳ tinh giản (`true`/`false`). Để toàn bộ phần xử lý giao diện nhạy bén (Responsive) cho CSS lo qua Media Queries. Sử dụng GPU-accelerated (`transform`) cho phần trượt đi và `transition` đồng bộ để tạo nhịp điệu chuyển động trơn tru.

---

## 9. Bài học rút ra (Transferable Lessons)

*   **Simple State + Rich CSS = Premium Experience:** Hãy giữ logic Javascript đơn giản nhất có thể. Sức mạnh thực sự của một UI mượt mà nằm ở sự thấu hiểu các thuộc tính CSS, tận dụng transition bezier và cách tổ chức class chuẩn BEM.
*   **Đồng bộ hóa Animation:** Khi có hai phần tử tương tác lẫn nhau trên màn hình, hãy luôn đảm bảo chúng dùng chung một bộ thông số transition (thời gian, kiểu easing). Sự chênh lệch dù chỉ là 0.05 giây cũng đủ để mắt người cảm thấy giao diện có gì đó "sai sai".

Chúc bạn có những giây phút trải nghiệm sidebar mới thật mượt mà bên ly cà phê nhé! ☕✨
