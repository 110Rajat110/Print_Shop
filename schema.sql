CREATE DATABASE IF NOT EXISTS `Print_Project`;
USE `Print_Project`;

/* Table 1: One entry per customer order "batch" */
CREATE TABLE IF NOT EXISTS `PrintBatches` (
    `batch_id` INT AUTO_INCREMENT,
    `mobile_number` VARCHAR(15) NOT NULL,
    `status` ENUM('Waiting', 'Printing', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Waiting',
    `total_cost` DECIMAL(10, 2) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`batch_id`)
);

/* Table 2: One entry for EACH file or file-part in a batch */
CREATE TABLE IF NOT EXISTS `PrintFiles` (
    `file_id` INT AUTO_INCREMENT,
    `batch_id` INT NOT NULL,
    `file_name_original` VARCHAR(255) NOT NULL,
    `file_path_saved` VARCHAR(255) NOT NULL,
    `page_count_original` INT NOT NULL,
    `page_range` VARCHAR(100) NOT NULL DEFAULT 'All',
    `page_count_final` INT NOT NULL,
    `copies` INT NOT NULL DEFAULT 1,
    `print_color` BOOLEAN NOT NULL DEFAULT 0,
    `print_duplex` BOOLEAN NOT NULL DEFAULT 0,
    `file_cost` DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (`file_id`),
    FOREIGN KEY (`batch_id`) REFERENCES `PrintBatches`(`batch_id`) ON DELETE CASCADE
);

/* Table 3: Stores the shop's prices */
CREATE TABLE IF NOT EXISTS `Settings` (
    `setting_key` VARCHAR(50) PRIMARY KEY,
    `setting_value` VARCHAR(100) NOT NULL
);

/* Insert default prices for calculation */
INSERT INTO `Settings` (setting_key, setting_value)
VALUES
    ('price_per_page_bw', '2.00'),
    ('price_per_page_color', '10.00'),
    ('price_duplex_multiplier', '1.8')
ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value);
