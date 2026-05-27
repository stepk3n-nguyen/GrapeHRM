-- GrapeHRM Database Seed Data (SQL)
-- Chỉ tạo cấu trúc ban đầu qua SQL.
-- Dữ liệu user/admin được seed bằng Python (app/seed.py) với bcrypt hash đúng.

-- Tạo tenant mặc định (công ty demo)
INSERT INTO tenants (id, name, slug, country, city, address, is_active) 
VALUES (1, 'GrapeCorp', 'grapecorp', 'Vietnam', 'Ho Chi Minh', '123 Grape Street, District 1', 1)
ON DUPLICATE KEY UPDATE name=name;
