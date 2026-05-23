-- GrapeHRM Database Schema
-- (This file is run when the database container is first initialized)

CREATE TABLE IF NOT EXISTS tenants (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    tax_id      VARCHAR(50),
    reg_number  VARCHAR(50),
    phone       VARCHAR(30),
    email       VARCHAR(100),
    country     VARCHAR(100),
    city        VARCHAR(100),
    address     VARCHAR(255),
    logo_url    VARCHAR(500),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id   INT NOT NULL,
    employee_id INT,
    username    VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role        ENUM('super_admin','admin','hr_manager','supervisor','employee') DEFAULT 'employee',
    is_active   BOOLEAN DEFAULT TRUE,
    last_login  DATETIME,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, username),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
