# setup.sh
#!/bin/bash
echo "🔧 Setting up Invoicing App..."

# Create directories
#mkdir -p static/css static/js templates database

# Create config.py if not exists
if [ ! -f "config.py" ]; then
    cat > config.py << 'EOF'
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DB_BASE_URL = 'http://localhost:5000/api'

class DevelopmentConfig(Config):
    DEBUG = True

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
EOF
    echo "✅ Created config.py"
fi

# Create simple init.sql
cat > database/init2.sql << 'EOF'
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
EOF
echo "✅ Created init.sql"

echo "✅ Setup complete!"
echo ""
echo "To start:"
echo "1. Start MyRDBMS: cd ~/Documents/Python\\ Projects/myrdbms && python3 api/server.py"
echo "2. Start Flask: python3 app.py"
echo "3. Open: http://localhost:8000"