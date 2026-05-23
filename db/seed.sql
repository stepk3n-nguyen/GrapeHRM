-- GrapeHRM Database Seed Data

-- Insert default tenant
INSERT INTO tenants (id, name, slug, country, city, address, is_active) 
VALUES (1, 'GrapeCorp', 'grapecorp', 'Vietnam', 'Ho Chi Minh', '123 Grape Street, District 1', 1)
ON DUPLICATE KEY UPDATE name=name;
