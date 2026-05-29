-- 1. Đổi tên bảng job_positions thành job_titles
RENAME TABLE job_positions TO job_titles;

-- 2. Đổi tên cột position_id trong employees thành title_id và cập nhật khóa ngoại
ALTER TABLE employees DROP FOREIGN KEY fk_employee_position;
ALTER TABLE employees CHANGE COLUMN position_id title_id INT NULL;
ALTER TABLE employees ADD CONSTRAINT fk_employee_title FOREIGN KEY (title_id) REFERENCES job_titles(id) ON DELETE SET NULL;

-- 3. Tạo bảng departments mới
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT fk_department_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- 4. Thêm cột department_id, end_date, address vào bảng employees và liên kết khóa ngoại
ALTER TABLE employees ADD COLUMN department_id INT NULL;
ALTER TABLE employees ADD COLUMN end_date DATE NULL;
ALTER TABLE employees ADD COLUMN address TEXT NULL;
ALTER TABLE employees ADD CONSTRAINT fk_employee_department FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL;
