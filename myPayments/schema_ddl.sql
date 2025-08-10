DROP DATABASE IF EXISTS my_payments_db;
CREATE DATABASE my_payments_db;
USE my_payments_db;

-- Customers
CREATE TABLE customer (
                          id INT AUTO_INCREMENT PRIMARY KEY,
                          full_name VARCHAR(100) NOT NULL,
                          email VARCHAR(100) NOT NULL UNIQUE,
                          phone_number VARCHAR(20),
                          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Transactions
CREATE TABLE transaction (
                             id INT AUTO_INCREMENT PRIMARY KEY,
                             customer_id INT NOT NULL,
                             amount DECIMAL(10, 2) NOT NULL,
                             currency VARCHAR(3) DEFAULT 'USD',
                             category VARCHAR(50),
                             status ENUM('PENDING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
                             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                             description VARCHAR(255),
                             FOREIGN KEY (customer_id) REFERENCES customer(id)
);

-- Payments
CREATE TABLE payment (
                         id INT AUTO_INCREMENT PRIMARY KEY,
                         transaction_id INT NOT NULL UNIQUE,
                         method VARCHAR(50),
                         status ENUM('INITIATED', 'SUCCESS', 'FAILED') DEFAULT 'INITIATED',
                         reference_id VARCHAR(100),
                         processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                         FOREIGN KEY (transaction_id) REFERENCES transaction(id)
);
