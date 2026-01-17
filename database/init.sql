-- database/init.sql
-- For RDBMS that uses positional INSERT syntax

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    company_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create other tables
CREATE TABLE IF NOT EXISTS customers (
    id INT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    country VARCHAR(50),
    tax_id VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    user_id INT NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    subtotal DECIMAL(10, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    amount_paid DECIMAL(10, 2) DEFAULT 0,
    balance_due DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    currency VARCHAR(3) DEFAULT 'KES',
    notes TEXT,
    terms TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id INT PRIMARY KEY,
    invoice_id INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2) DEFAULT 1,
    unit_price DECIMAL(10, 2) DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    amount DECIMAL(10, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount DECIMAL(10, 2) DEFAULT 0,
    payment_method VARCHAR(50),
    reference_number VARCHAR(100),
    payment_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Insert demo user (password: demo123)
-- Positional INSERT syntax: VALUES (value1, value2, value3, ...)
INSERT INTO users VALUES (1, 'demo', 'demo@invoicing.com', 'd3ad9315b7be5dd53b31a273b3b3aba5defe700808305aa16a3062b76658a791', 'Demo User', 'Demo Company Inc.', CURRENT_TIMESTAMP, NULL, TRUE);

-- Insert sample customers
INSERT INTO customers VALUES (1, 1, 'Acme Corporation', 'billing@acme.com', '+254700123456', '123 Business Street', 'Nairobi', 'Kenya', 'TAX-001', 'Regular customer', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO customers VALUES (2, 1, 'Tech Solutions Ltd', 'accounts@techsolutions.co.ke', '+254711987654', '456 Tech Avenue', 'Mombasa', 'Kenya', 'TAX-002', 'IT services provider', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO customers VALUES (3, 1, 'Green Energy Africa', 'finance@greenenergy.africa', '+254722555555', '789 Green Road', 'Kampala', 'Uganda', 'TAX-003', 'Renewable energy company', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Insert sample invoices
INSERT INTO invoices VALUES (1, 1, 1, 'INV-2024-001', '2024-01-15', '2024-02-14', 1500.00, 150.00, 1650.00, 1650.00, 0.00, 'paid', 'KES', 'Thank you for your business!', 'Payment due in 30 days', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO invoices VALUES (2, 2, 1, 'INV-2024-002', '2024-01-20', '2024-02-19', 2750.00, 275.00, 3025.00, 1000.00, 2025.00, 'sent', 'KES', 'Software implementation', 'Net 30', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
INSERT INTO invoices VALUES (3, 3, 1, 'INV-2024-003', '2024-01-25', '2024-02-24', 980.00, 98.00, 1078.00, 0.00, 1078.00, 'draft', 'KES', 'Consulting services', 'Upon receipt', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Insert invoice items
INSERT INTO invoice_items VALUES (1, 1, 'Website Design Service', 1, 1000.00, 10, 1000.00, 100.00, 1100.00, CURRENT_TIMESTAMP);
INSERT INTO invoice_items VALUES (2, 1, 'Hosting Setup', 1, 500.00, 10, 500.00, 50.00, 550.00, CURRENT_TIMESTAMP);
INSERT INTO invoice_items VALUES (3, 2, 'Software License', 2, 1000.00, 10, 2000.00, 200.00, 2200.00, CURRENT_TIMESTAMP);
INSERT INTO invoice_items VALUES (4, 2, 'Implementation Support', 1, 750.00, 10, 750.00, 75.00, 825.00, CURRENT_TIMESTAMP);
INSERT INTO invoice_items VALUES (5, 3, 'Consulting Hours', 8, 100.00, 10, 800.00, 80.00, 880.00, CURRENT_TIMESTAMP);
INSERT INTO invoice_items VALUES (6, 3, 'Travel Expenses', 1, 180.00, 10, 180.00, 18.00, 198.00, CURRENT_TIMESTAMP);

-- Insert sample payments
INSERT INTO payments VALUES (1, 1, 1650.00, 'bank_transfer', 'TRX-001234', '2024-02-10', 'Full payment received', CURRENT_TIMESTAMP);
INSERT INTO payments VALUES (2, 2, 1000.00, 'mobile_money', 'MPESA-ABC123', '2024-02-15', 'Partial payment', CURRENT_TIMESTAMP);