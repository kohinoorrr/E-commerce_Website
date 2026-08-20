-- =============================================================
-- Seed Data for eco_ecommerce
-- =============================================================

-- ---------------------------------------------------------------
-- Admin + sample users  (passwords are bcrypt hashes of shown values)
-- admin@eco.com  → password: admin123
-- jane@eco.com   → password: user123
-- ---------------------------------------------------------------
INSERT INTO users (name, email, password, address, phone, is_admin) VALUES
('Admin User',  'admin@eco.com', 'admin123',   '1 Green Lane, EcoCity', '9000000001', TRUE),
('Jane Doe',    'jane@eco.com',  'user123',    '22 Maple St, Springfield', '9000000002', FALSE),
('Ravi Kumar',  'ravi@eco.com',  'user123',    '5 Park Ave, Mumbai', '9000000003', FALSE);

-- NOTE: In production the app hashes passwords with Werkzeug.
-- The seed uses plain strings; run /signup or use the admin panel in real usage.

-- ---------------------------------------------------------------
-- Categories
-- ---------------------------------------------------------------
INSERT INTO categories (category_name) VALUES
('Electronics'),          -- id 1 → High emission
('Clothing'),             -- id 2 → Medium emission
('Food & Beverages'),     -- id 3 → Medium emission
('Reusable & Eco Goods'), -- id 4 → Low emission
('Furniture'),            -- id 5 → High emission
('Books & Stationery');   -- id 6 → Low emission

-- ---------------------------------------------------------------
-- Products  (base_carbon_emission in kg CO₂e per unit)
-- ---------------------------------------------------------------
INSERT INTO products (name, description, price, stock, category_id, base_carbon_emission, carbon_level) VALUES

-- Electronics → High
('Laptop Pro 15',
 'High-performance laptop with 15-inch display, 16GB RAM, aluminum chassis. Manufacturing involves energy-intensive processes.',
 89999.00, 50, 1, 350.00, 'high'),

('Bluetooth Speaker',
 'Portable wireless speaker with 12-hour battery life. Uses lithium-ion battery and plastic enclosure.',
 3499.00, 120, 1, 18.50, 'medium'),

('Smartphone X12',
 'Latest flagship smartphone with OLED display, 5G, titanium frame. High chip fabrication emission.',
 74999.00, 80, 1, 70.00, 'high'),

('LED Desk Lamp',
 'Energy-efficient LED desk lamp with USB charging port. Low power consumption during use.',
 999.00, 200, 1, 5.20, 'low'),

-- Clothing → Medium
('Organic Cotton T-Shirt',
 'Sustainably farmed organic cotton t-shirt, GOTS certified, natural dyes used.',
 799.00, 300, 2, 2.10, 'low'),

('Denim Jeans',
 'Classic denim jeans made with water-intensive cotton farming and synthetic dyes.',
 2499.00, 180, 2, 33.40, 'high'),

('Recycled Polyester Jacket',
 'Jacket made from 100% recycled plastic bottles. Reduces landfill and carbon footprint.',
 3999.00, 90, 2, 7.80, 'medium'),

-- Food & Beverages → Medium
('Organic Green Tea (100g)',
 'Certified organic green tea, sun-dried, minimal processing, locally sourced.',
 349.00, 500, 3, 0.50, 'low'),

('Instant Coffee Jar (200g)',
 'Imported instant coffee requiring freight shipping and energy-intensive freeze-drying.',
 599.00, 400, 3, 4.60, 'medium'),

-- Reusable & Eco Goods → Low
('Stainless Steel Water Bottle',
 'BPA-free, reusable 1L water bottle replacing up to 1000 single-use plastic bottles.',
 699.00, 600, 4, 1.20, 'low'),

('Bamboo Toothbrush (Pack of 4)',
 'Biodegradable bamboo toothbrush. Carbon sequestration during bamboo growth offsets production.',
 299.00, 800, 4, 0.30, 'low'),

('Beeswax Food Wraps (Set of 3)',
 'Reusable alternative to plastic cling wrap. Handmade, zero synthetic chemicals.',
 499.00, 350, 4, 0.80, 'low'),

-- Furniture → High
('Wooden Office Chair',
 'Solid teak office chair. Wood harvesting and lacquer coating contribute to carbon output.',
 12999.00, 40, 5, 95.00, 'high'),

-- Books & Stationery → Low
('Seed Paper Notebook',
 'Recycled paper notebook embedded with wildflower seeds. Plant it after use!',
 249.00, 700, 6, 0.60, 'low'),

('Bestseller Novel – EcoFutures',
 'Fiction novel printed on FSC-certified recycled paper with soy-based inks.',
 399.00, 500, 6, 1.10, 'low');
