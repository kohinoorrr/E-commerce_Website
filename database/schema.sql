-- =============================================================
-- E-Commerce Sustainability Management System
-- Database: eco_ecommerce (PostgreSQL)
-- =============================================================

-- Create & connect to the database (run this in psql or pgAdmin)
-- CREATE DATABASE eco_ecommerce;
-- \c eco_ecommerce

-- Drop tables if re-running (order matters due to FK dependencies)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS cart CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ---------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------
CREATE TABLE users (
    user_id   SERIAL PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(150) NOT NULL UNIQUE,
    password  VARCHAR(255) NOT NULL,   -- stored as hashed value
    address   TEXT,
    phone     VARCHAR(20),
    is_admin  BOOLEAN DEFAULT FALSE,
    is_merchant BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- Categories
-- ---------------------------------------------------------------
CREATE TABLE categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------
-- Products
-- ---------------------------------------------------------------
CREATE TABLE products (
    product_id          SERIAL PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    price               NUMERIC(10, 2) NOT NULL,
    stock               INT NOT NULL DEFAULT 0,
    category_id         INT REFERENCES categories(category_id) ON DELETE SET NULL,
    base_carbon_emission NUMERIC(10, 4) NOT NULL DEFAULT 0.0,
    -- carbon_level: 'low' | 'medium' | 'high'  (AI-predicted label stored here)
    carbon_level        VARCHAR(10) DEFAULT 'medium',
    merchant_id         INT REFERENCES users(user_id) ON DELETE CASCADE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- Cart  (one active cart per user)
-- ---------------------------------------------------------------
CREATE TABLE cart (
    cart_id    SERIAL PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- Cart Items
-- ---------------------------------------------------------------
CREATE TABLE cart_items (
    cart_item_id SERIAL PRIMARY KEY,
    cart_id      INT NOT NULL REFERENCES cart(cart_id) ON DELETE CASCADE,
    product_id   INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    quantity     INT NOT NULL DEFAULT 1 CHECK (quantity > 0)
);

-- ---------------------------------------------------------------
-- Orders
-- ---------------------------------------------------------------
CREATE TABLE orders (
    order_id         SERIAL PRIMARY KEY,
    user_id          INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    order_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount     NUMERIC(10, 2) NOT NULL,
    total_carbon     NUMERIC(10, 4) DEFAULT 0.0,
    status           VARCHAR(30) DEFAULT 'completed'
);

-- ---------------------------------------------------------------
-- Order Items
-- ---------------------------------------------------------------
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id    INT NOT NULL REFERENCES products(product_id) ON DELETE SET NULL,
    quantity      INT NOT NULL,
    price         NUMERIC(10, 2) NOT NULL,
    carbon_contribution NUMERIC(10, 4) DEFAULT 0.0
);

-- ---------------------------------------------------------------
-- Useful Views
-- ---------------------------------------------------------------

-- View: Cart summary with carbon per item
CREATE OR REPLACE VIEW cart_summary AS
SELECT
    ci.cart_id,
    ci.cart_item_id,
    p.product_id,
    p.name          AS product_name,
    p.price,
    p.base_carbon_emission,
    ci.quantity,
    (p.price * ci.quantity)                   AS item_total,
    (p.base_carbon_emission * ci.quantity)    AS item_carbon,
    p.carbon_level
FROM cart_items ci
JOIN products p ON ci.product_id = p.product_id;

-- View: Order summary with total carbon
CREATE OR REPLACE VIEW order_summary AS
SELECT
    o.order_id,
    o.user_id,
    u.name          AS user_name,
    o.order_date,
    o.total_amount,
    o.total_carbon,
    o.status
FROM orders o
JOIN users u ON o.user_id = u.user_id;

-- View: Carbon analytics
CREATE OR REPLACE VIEW carbon_analytics AS
SELECT
    COUNT(*)                    AS total_orders,
    SUM(total_carbon)           AS total_emissions_kg,
    AVG(total_carbon)           AS avg_carbon_per_order,
    MAX(total_carbon)           AS max_carbon_order,
    MIN(total_carbon)           AS min_carbon_order
FROM orders;
