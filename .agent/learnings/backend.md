# Backend

> Tổng hợp kiến thức về backend infrastructure, Docker deployment và Flask API trong dự án GrapeHRM.
> Cập nhật lần cuối: 2026-05-24

---

## Architecture

### Docker Compose 3-Service Architecture
- **Ngày**: 2026-05-24
- **Chi tiết**: Dự án chạy 3 Docker containers: `db` (MySQL 8.0), `api` (Flask), `frontend` (Vite React). Service `api` depends_on `db`, `frontend` depends_on `api` — đảm bảo thứ tự khởi động. Tất cả biến nhạy cảm (DB password, JWT secret) đặt trong `.env` và tham chiếu qua `${VAR}` syntax — file `.env` đã thêm vào `.gitignore`.
- **Files liên quan**: `docker-compose.yml`, `.env`, `.gitignore`

### MySQL 8 Authentication Plugin
- **Ngày**: 2026-05-24
- **Chi tiết**: MySQL 8 mặc định dùng `caching_sha2_password`, nhưng nhiều driver Python (PyMySQL) chưa hỗ trợ tốt. Buộc phải thêm `command: --default-authentication-plugin=mysql_native_password` trong docker-compose để dùng plugin cũ tương thích hơn.
- **Files liên quan**: `docker-compose.yml`

---

## Bugs & Solutions

### PowerShell không hỗ trợ toán tử `&&`
- **Ngày**: 2026-05-24
- **Vấn đề**: Chạy `git add ... && git commit ...` trên PowerShell báo lỗi `The token '&&' is not a valid statement separator`.
- **Root cause**: PowerShell (phiên bản < 7) không hỗ trợ `&&` như bash. Chỉ PowerShell 7+ mới có.
- **Fix**: Dùng dấu `;` thay thế: `git add ... ; git commit ...`. Lưu ý: `;` chạy lệnh tiếp theo bất kể lệnh trước thành công hay thất bại (khác với `&&`).
- **Files liên quan**: *(terminal command)*

### Lỗi import pprint từ marshmallow v4
- **Ngày**: 2026-05-24
- **Task**: Cài đặt thư viện và khởi động server backend
- **Chi tiết**: `flask-marshmallow==1.2.*` bị lỗi khi tải về `marshmallow>=4.0.0` do thư viện gốc đã xóa module `pprint`. 
- **Cách fix**: Cần ghim cứng phiên bản `marshmallow<4.0.0` trong `requirements.txt`.
- **Files liên quan**: `backend/requirements.txt`

### Lỗi Docker Desktop unable to start trên Windows
- **Ngày**: 2026-05-24
- **Task**: Cài đặt thư viện và khởi động server backend
- **Chi tiết**: Khi chạy docker compose gặp lỗi `Docker Desktop is unable to start`. Root cause do WSL quá cũ trên Windows.
- **Cách fix**: Chạy lệnh `wsl --update` bằng quyền Admin và bắt buộc khởi động lại máy tính để Windows nhận lõi WSL mới.
- **Files liên quan**: *(Windows CLI)*

---

## How-To

### Cách cấu hình Docker Compose cho dự án full-stack mới
- **Ngày**: 2026-05-24
- **Bước thực hiện**:
  1. Tạo `.env` chứa tất cả secrets (DB password, JWT key). Thêm `.env` vào `.gitignore`.
  2. Tạo `docker-compose.yml` với 3 services: `db`, `api`, `frontend`.
  3. Dùng `volumes` named (`mysql_data:`) cho database persistence, bind-mount code folder cho hot-reload dev.
  4. Frontend mount thêm anonymous volume `/app/node_modules` để tránh conflict giữa host và container node_modules.
  5. Đặt SQL init scripts vào `db/` và mount vào `/docker-entrypoint-initdb.d/`.
- **Files liên quan**: `docker-compose.yml`, `.env`

---

## Patterns

### Environment Variable Reference trong Docker Compose
- **Ngày**: 2026-05-24
- **Chi tiết**: Dùng `${VARIABLE}` syntax trong `docker-compose.yml` để tham chiếu biến từ file `.env` cùng thư mục. Docker Compose tự động đọc `.env` — không cần khai báo `env_file:` riêng. Ví dụ: `DATABASE_URL: mysql+pymysql://${DB_USER}:${DB_PASSWORD}@db:3306/${MYSQL_DATABASE}` — string connection tổ hợp từ nhiều biến.
- **Ví dụ code**:
  ```yaml
  environment:
    DATABASE_URL: mysql+pymysql://${DB_USER}:${DB_PASSWORD}@db:3306/${MYSQL_DATABASE}
  ```
- **Files liên quan**: `docker-compose.yml`, `.env`

### Volume Strategy: Named vs Bind-Mount vs Anonymous
- **Ngày**: 2026-05-24
- **Chi tiết**: Dự án dùng 3 loại volume: (1) **Named volume** `mysql_data` cho DB persistence — data tồn tại sau `docker-compose down`. (2) **Bind-mount** `./backend:/app` cho hot-reload code. (3) **Anonymous volume** `/app/node_modules` cho frontend — ngăn node_modules trên host ghi đè node_modules trong container (vì platform khác nhau).
- **Files liên quan**: `docker-compose.yml`
