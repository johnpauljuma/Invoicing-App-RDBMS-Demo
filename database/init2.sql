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

INSERT INTO users VALUES (1, 'demo', 'demo@invoicing.com', 
       'c96c6d5be8d08a12e7b5cdc1b207fa6b2430974cce03f3b153f416c2f9bb54e8:abc123def456', 
       'Demo User', 'Demo Company Inc.')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = 1);
