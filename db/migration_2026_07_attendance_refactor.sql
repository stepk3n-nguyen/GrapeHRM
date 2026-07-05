-- ============================================================================
-- GrapeHRM — Migration 07/2026: Refactor xoay quanh Attendance
--
-- LƯU Ý: Migration này chạy TỰ ĐỘNG khi khởi động backend
-- (app/services/schema_upgrade.py). File này chỉ dành cho DBA muốn chạy tay
-- trên MySQL production, hoặc để tham khảo các thay đổi schema.
--
-- Database mới không cần file này: `python run.py` tự tạo toàn bộ bảng,
-- sau đó `python seed_demo.py` tạo dữ liệu demo.
-- ============================================================================

USE grapehrm;

-- 1. Chấm công: thêm số phút đi muộn / về sớm + trạng thái VỀ SỚM
ALTER TABLE attendance ADD COLUMN late_minutes  INTEGER NOT NULL DEFAULT 0;
ALTER TABLE attendance ADD COLUMN early_minutes INTEGER NOT NULL DEFAULT 0;
ALTER TABLE attendance MODIFY COLUMN status
  ENUM('PRESENT','ABSENT','LATE','EARLY_LEAVE','HALF_DAY','ON_LEAVE') NOT NULL;

-- 2. Nhân viên: gán ca làm việc riêng (NULL = dùng ca mặc định của công ty)
ALTER TABLE employees ADD COLUMN shift_id INTEGER NULL;
ALTER TABLE employees ADD CONSTRAINT fk_employees_shift
  FOREIGN KEY (shift_id) REFERENCES work_shifts(id) ON DELETE SET NULL;

-- 3. Gỡ các module demo khỏi MVP (không đủ dữ liệu vận hành thực tế):
--    Hợp đồng (không mẫu/PDF/ký số), Tuyển dụng, Đánh giá hiệu suất
DROP TABLE IF EXISTS review_scores;
DROP TABLE IF EXISTS performance_reviews;
DROP TABLE IF EXISTS review_cycles;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS job_postings;
DROP TABLE IF EXISTS contracts;
