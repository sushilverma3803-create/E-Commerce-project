-- ============================================================================
-- E-Commerce Platform Database Schema
-- Architecture Specification: MySQL 8.0+ / MariaDB 10.5+
-- Storage Engine: InnoDB
-- Character Set: utf8mb4 (Collation: utf8mb4_unicode_ci)
-- ============================================================================

-- Disable foreign key checks during initialization
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO,STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
SET NAMES utf8mb4;

-- ----------------------------------------------------------------------------
-- Database Initialization
-- ----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS `ecommerce_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `ecommerce_db`;

-- Drop existing tables in reverse dependency order (idempotent setup)
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `cart`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;

-- ============================================================================
-- 1. USERS TABLE
-- Handles authentication, roles, contact details, and account lifecycle
-- ============================================================================
CREATE TABLE `users` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('customer', 'admin') NOT NULL DEFAULT 'customer',
    `phone` VARCHAR(20) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_users_email` (`email`),
    KEY `idx_users_role` (`role`),
    KEY `idx_users_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User profiles and credentials';

-- ============================================================================
-- 2. CATEGORIES TABLE
-- Hierarchical product grouping with SEO-friendly slugs
-- ============================================================================
CREATE TABLE `categories` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `slug` VARCHAR(120) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `image_url` VARCHAR(500) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_categories_slug` (`slug`),
    KEY `idx_categories_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Product categories taxonomy';

-- ============================================================================
-- 3. PRODUCTS TABLE
-- Catalog inventory, monetary pricing, stock control, and foreign taxonomy
-- ============================================================================
CREATE TABLE `products` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` BIGINT UNSIGNED NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(280) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `stock` INT UNSIGNED NOT NULL DEFAULT 0,
    `image_url` VARCHAR(500) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_products_slug` (`slug`),
    KEY `idx_products_category_id` (`category_id`),
    KEY `idx_products_price` (`price`),
    KEY `idx_products_created_at` (`created_at`),
    KEY `idx_products_stock` (`stock`),
    
    CONSTRAINT `chk_products_price` CHECK (`price` >= 0.00),
    CONSTRAINT `fk_products_category`
        FOREIGN KEY (`category_id`)
        REFERENCES `categories` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Product inventory catalog';

-- ============================================================================
-- 4. CART TABLE
-- Active user shopping basket; enforced uniqueness per user-product pairing
-- ============================================================================
CREATE TABLE `cart` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `product_id` BIGINT UNSIGNED NOT NULL,
    `quantity` INT UNSIGNED NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_cart_user_product` (`user_id`, `product_id`),
    KEY `idx_cart_user_id` (`user_id`),
    KEY `idx_cart_product_id` (`product_id`),
    
    CONSTRAINT `chk_cart_quantity` CHECK (`quantity` > 0),
    CONSTRAINT `fk_cart_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_cart_product`
        FOREIGN KEY (`product_id`)
        REFERENCES `products` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Shopping cart items';

-- ============================================================================
-- 5. ORDERS TABLE
-- Purchase orders with delivery destination and financial aggregate
-- ============================================================================
CREATE TABLE `orders` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `total_amount` DECIMAL(12, 2) NOT NULL,
    `status` ENUM('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Pending',
    `shipping_address` TEXT NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_orders_user_id` (`user_id`),
    KEY `idx_orders_status` (`status`),
    KEY `idx_orders_created_at` (`created_at`),
    KEY `idx_orders_user_status` (`user_id`, `status`),
    
    CONSTRAINT `chk_orders_total_amount` CHECK (`total_amount` >= 0.00),
    CONSTRAINT `fk_orders_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Customer order transactions';

-- ============================================================================
-- 6. ORDER_ITEMS TABLE
-- Line items capturing item snapshot price at moment of sale
-- ============================================================================
CREATE TABLE `order_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id` BIGINT UNSIGNED NOT NULL,
    `product_id` BIGINT UNSIGNED NOT NULL,
    `quantity` INT UNSIGNED NOT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    
    PRIMARY KEY (`id`),
    KEY `idx_order_items_order_id` (`order_id`),
    KEY `idx_order_items_product_id` (`product_id`),
    
    CONSTRAINT `chk_order_items_quantity` CHECK (`quantity` > 0),
    CONSTRAINT `chk_order_items_price` CHECK (`price` >= 0.00),
    CONSTRAINT `fk_order_items_order`
        FOREIGN KEY (`order_id`)
        REFERENCES `orders` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_order_items_product`
        FOREIGN KEY (`product_id`)
        REFERENCES `products` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Order line items with immutable price snapshot';

-- ============================================================================
-- 7. PAYMENTS TABLE
-- Payment ledger recording gateway transaction references and statuses
-- ============================================================================
CREATE TABLE `payments` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id` BIGINT UNSIGNED NOT NULL,
    `payment_gateway` VARCHAR(50) NOT NULL,
    `transaction_id` VARCHAR(100) NOT NULL,
    `amount` DECIMAL(12, 2) NOT NULL,
    `status` ENUM('Success', 'Failed', 'Pending') NOT NULL DEFAULT 'Pending',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_payments_transaction_id` (`transaction_id`),
    KEY `idx_payments_order_id` (`order_id`),
    KEY `idx_payments_status` (`status`),
    KEY `idx_payments_gateway_status` (`payment_gateway`, `status`),
    
    CONSTRAINT `chk_payments_amount` CHECK (`amount` >= 0.00),
    CONSTRAINT `fk_payments_order`
        FOREIGN KEY (`order_id`)
        REFERENCES `orders` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Payment gateway reconciliation ledger';

-- Re-enable foreign key constraints
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- SEED DATA INSERT STATEMENTS
-- ============================================================================

-- Categories Seed Data
INSERT INTO `categories` (`id`, `name`, `slug`, `description`, `image_url`) VALUES
(1, 'Electronics', 'electronics', 'Smartphones, laptops, accessories, and consumer gadgets', 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800'),
(2, 'Footwear & Fashion', 'footwear-fashion', 'Sneakers, formal shoes, apparel, and lifestyle wear', 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800'),
(3, 'Home & Living', 'home-living', 'Modern ergonomic furniture, smart lighting, and kitchenware', 'https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800'),
(4, 'Health & Fitness', 'health-fitness', 'Workout equipment, supplements, and wellness essentials', 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800');

-- Products Seed Data
INSERT INTO `products` (`id`, `category_id`, `name`, `slug`, `description`, `price`, `stock`, `image_url`) VALUES
-- Electronics
(1, 1, 'ProSound Wireless Noise-Cancelling Headphones', 'prosound-wireless-headphones', 'Over-ear active noise cancelling Bluetooth 5.3 headphones with 40h battery life.', 249.99, 45, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800'),
(2, 1, 'UltraBook Pro 15.6" Retina', 'ultrabook-pro-15', 'High-performance laptop with 32GB RAM, 1TB NVMe SSD, and 12-core CPU.', 1499.00, 20, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800'),
(3, 1, 'PixelWatch Horizon Smartwatch', 'pixelwatch-horizon-smartwatch', 'AMOLED display smartwatch with heart rate sensor, GPS tracking, and 7-day battery.', 199.50, 75, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800'),

-- Footwear & Fashion
(4, 2, 'AeroStride Runner Pro Shoes', 'aerostride-runner-pro-shoes', 'Breathable knit cushioning running sneakers designed for marathon and daily workouts.', 129.95, 60, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800'),
(5, 2, 'Heritage Classic Leather Oxford Shoes', 'heritage-classic-leather-oxford', 'Handcrafted genuine leather formal dress shoes with durable Goodyear welt sole.', 185.00, 30, 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=800'),

-- Home & Living
(6, 3, 'ErgoFlex Ergonomic Mesh Office Chair', 'ergoflex-ergonomic-mesh-chair', 'Adjustable lumbar support chair with 3D armrests and breathable elastomeric mesh.', 319.00, 15, 'https://images.unsplash.com/photo-1580481077195-c9f563603953?w=800'),
(7, 3, 'Minimalist Solid Oak Coffee Table', 'minimalist-solid-oak-coffee-table', 'Scandinavian handcrafted natural oak table featuring soft rounded safety edges.', 220.00, 12, 'https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=800'),

-- Health & Fitness
(8, 4, 'HexGrip Rubber Cast Iron Dumbbells (Pair 20kg)', 'hexgrip-rubber-dumbbells-20kg', 'Anti-roll hex rubber coated gym dumbbells with contoured knurled chrome handles.', 89.90, 40, 'https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=800');
