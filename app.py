# app.py - Fixed version for Flask 2.3+
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps
import logging
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'invoicing-app-secret-key-2024'  # Simple key for development

# Database connection to your RDBMS
DB_API_BASE = 'http://localhost:5000/api'

class DatabaseManager:
    """Interface to your MyRDBMS database"""
    
    def __init__(self, db_name='invoicing_db'):
        self.db_name = db_name
        self.base_url = f"{DB_API_BASE}/databases/{db_name}"
        self.initialized = False
        self.initializing = False
    
    def database_exists(self):
        """Check if database exists"""
        try:
            response = requests.get(f"{DB_API_BASE}/databases/{self.db_name}", timeout=5)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def create_database(self):
        """Create the database if it doesn't exist"""
        if self.database_exists():
            logger.info(f"Database '{self.db_name}' already exists")
            return True
        
        try:
            logger.info(f"Creating database '{self.db_name}'...")
            response = requests.post(
                f"{DB_API_BASE}/databases",
                json={'name': self.db_name},
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"Database '{self.db_name}' created successfully")
                return True
            else:
                logger.error(f"Failed to create database: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False
    
    def execute(self, query):
        """Execute a SQL query"""
        try:
            # Try to execute query
            response = requests.post(
                f"{self.base_url}/execute",
                json={'query': query},
                timeout=10
            )
            return response.json()
        except Exception as e:
            logger.error(f"Database error: {e}")
            return {'success': False, 'error': str(e)}
    
    def table_exists(self, table_name):
        """Check if a specific table exists"""
        try:
            # Try to select from the table
            query = f"SELECT 1 FROM {table_name} LIMIT 1"
            result = self.execute(query)
            return result.get('success', False)
        except:
            return False
    
    def init_database(self, force=False):
        """Initialize database with schema (tables and data)"""
        if self.initialized and not force:
            logger.info("Database already initialized")
            return True
        
        if self.initializing:
            logger.info("Database initialization already in progress")
            return False
        
        self.initializing = True
        
        try:
            logger.info("Starting database initialization...")
            
            # Step 1: Create database if it doesn't exist
            if not self.create_database():
                logger.error("Failed to create database")
                self.initializing = False
                return False
            
            # Step 2: Read and execute the schema
            try:
                with open('database/init.sql', 'r') as f:
                    sql_content = f.read()
            except FileNotFoundError:
                logger.error("init.sql file not found")
                self.initializing = False
                return False
            
            # Split into individual statements
            statements = []
            current_statement = []
            
            for line in sql_content.split('\n'):
                line = line.strip()
                if not line or line.startswith('--'):  # Skip empty lines and comments
                    continue
                
                current_statement.append(line)
                
                if line.endswith(';'):
                    full_statement = ' '.join(current_statement)
                    statements.append(full_statement)
                    current_statement = []
            
            # Add any remaining statement
            if current_statement:
                statements.append(' '.join(current_statement))
            
            # Step 3: Execute each statement
            success_count = 0
            total_statements = len(statements)
            
            for i, statement in enumerate(statements, 1):
                logger.info(f"Executing statement {i}/{total_statements}: {statement[:50]}...")
                result = self.execute(statement)
                
                if result.get('success'):
                    success_count += 1
                else:
                    error = result.get('error', 'Unknown error')
                    # Check if error is because table already exists (that's usually fine)
                    if 'already exists' in str(error).lower() or 'duplicate' in str(error).lower():
                        success_count += 1
                        logger.warning(f"Table may already exist: {error}")
                    else:
                        logger.error(f"Failed to execute statement: {error}")
            
            logger.info(f"Database initialization complete: {success_count}/{total_statements} statements successful")
            
            if success_count >= total_statements * 0.8:  # 80% success rate is acceptable
                self.initialized = True
                self.initializing = False
                return True
            else:
                self.initializing = False
                return False
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            self.initializing = False
            return False
    
    def health_check(self):
        """Check if MyRDBMS is accessible"""
        try:
            # Check if we can connect to MyRDBMS
            response = requests.get(f"{DB_API_BASE}/health", timeout=3)
            return response.status_code == 200
        except Exception as e:
            return False

db = DatabaseManager()

def initialize_application():
    """Initialize application and database"""
    logger.info("=" * 50)
    logger.info("Starting Invoicing App")
    logger.info("=" * 50)
    
    # Check if MyRDBMS is running
    logger.info("Checking MyRDBMS connection...")
    
    if db.health_check():
        logger.info("✅ MyRDBMS is running")
        
        # Try to initialize database
        logger.info("Initializing database...")
        if db.init_database():
            logger.info("✅ Database initialized successfully")
        else:
            logger.warning("⚠️ Database initialization had issues")
    else:
        logger.warning("⚠️ MyRDBMS is not running")
        logger.info("The app will start, but database features won't work.")
        logger.info("To start MyRDBMS: cd ~/Documents/Python\\ Projects/myrdbms && python3 api/server.py")
    
    logger.info("=" * 50)
    logger.info("App is ready! Visit http://localhost:8000")
    logger.info("=" * 50)

# Start initialization in background thread
init_thread = threading.Thread(target=initialize_application, daemon=True)
init_thread.start()

# Add static file serving routes
@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory('static', 'favicon.ico')
    except:
        import base64
        favicon_data = base64.b64decode(b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAA2SURBVDhPYxgFgxiwjAI0AQYGRjScVjAqANQAoAEYGRnRcFpBmglgYmIahZQAAH8GA0J0Oxh5AAAAAElFTkSuQmCC")
        return favicon_data, 200, {'Content-Type': 'image/x-icon'}

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# Authentication utilities
# Update the hash_password and verify_password functions:

def hash_password(password):
    """Hash password - match the demo user's hash format"""
    # The demo user has this hash: d3ad9315b7be5dd53b31a273b3b3aba5defe700808305aa16a3062b76658a791
    # This looks like SHA-256 without salt
    hash_obj = hashlib.sha256(password.encode())
    return hash_obj.hexdigest()

def verify_password(stored_hash, password):
    """Verify password - simple SHA-256 without salt"""
    try:
        test_hash = hashlib.sha256(password.encode()).hexdigest()
        return stored_hash == test_hash
    except:
        return False
    
def create_session(user_id, ip_address=None, user_agent=None):
    # Check if sessions table exists
    table_check_query = "SELECT 1 FROM sessions LIMIT 1"
    table_check_result = db.execute(table_check_query)
    
    # If table doesn't exist (query fails), create it
    if not table_check_result.get('success'):
        logger.info("Sessions table doesn't exist, creating it...")
        
        # Create users table with proper schema
        create_table_query = """
            CREATE TABLE sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT
            )
        """
        
        create_table_result = db.execute(create_table_query)
        
        if not create_table_result.get('success'):
            logger.error(f"Failed to create users table: {create_table_result.get('error')}")
                
    """Create a new session"""
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)
    expires_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
    created_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Positional INSERT for sessions table
    # Columns: session_id, user_id, created_at, expires_at, ip_address, user_agent
    query = f"""
        INSERT INTO sessions VALUES (
            '{session_id}', 
            {user_id}, 
            '{created_str}', 
            '{expires_str}', 
            '{ip_address or ''}', 
            '{user_agent or ''}'
        )
    """
    
    logger.info(f"Creating session: {query[:100]}...")
    result = db.execute(query)
    
    if result.get('success'):
        return session_id
    
    logger.error(f"Failed to create session: {result.get('error')}")
    return None

def validate_session(session_id):
    """Validate session and return user data"""
    query = f"""
        SELECT s.*, u.id as user_id, u.username, u.email, u.full_name, u.company_name
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_id = '{session_id}'
        AND s.expires_at > '{datetime.now().isoformat()}'
        AND u.is_active = TRUE
    """
    
    result = db.execute(query)
    if result.get('success') and result.get('data'):
        return result['data'][0]
    return None

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is in session (simplified for now)
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login_page'))
        
        # Try to validate session from database
        session_id = request.cookies.get('session_id') or session.get('session_id')
        if session_id:
            user_data = validate_session(session_id)
            if user_data:
                request.user = user_data
                return f(*args, **kwargs)
        
        # Fallback to session data
        request.user = {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'email': session.get('email'),
            'full_name': session.get('full_name', ''),
            'company_name': session.get('company_name', '')
        }
        
        return f(*args, **kwargs)
    
    return decorated_function

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Redirect to login or dashboard"""
    session_id = request.cookies.get('session_id')
    if session_id and validate_session(session_id):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

# Page 1: Login
# Page 1: Login Page (GET)
@app.route('/login', methods=['GET'])
def login_page():
    """Render login page"""
    return render_template('login.html')

# Login Action (POST)
@app.route('/login', methods=['POST'])
def login_action():
    """Handle login form submission"""
    try:
        data = request.json if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        logger.info(f"Login attempt for email: {email}")
        
        # Find user by email
        query = f"SELECT * FROM users WHERE email = '{email}' AND is_active = TRUE"
        result = db.execute(query)
        
        if not result.get('success'):
            logger.error(f"Database error: {result.get('error')}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        
        if not result.get('data'):
            logger.warning(f"No user found for email: {email}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        user = result['data'][0]
        
        # Debug: Check password hash
        logger.info(f"User found: {user['email']}")
        
        # Verify password
        if not verify_password(user['password_hash'], password):
            logger.warning(f"Invalid password for user: {user['email']}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Create session
        session_id = create_session(
            user['id'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Failed to create session'}), 500
        
        # Update last login
        last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(f"""
            UPDATE users SET last_login = '{last_login}'
            WHERE id = {user['id']}
        """)
        
        response_data = {
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'company_name': user['company_name']
            },
            'session_id': session_id,
            'redirect': '/dashboard'
        }
        
        response = jsonify(response_data)
        response.set_cookie('session_id', session_id, 
                          httponly=True, 
                          max_age=86400,
                          samesite='Lax')
        
        return response
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Server error'}), 500

# Page 1a: Register Page (GET)
@app.route('/register', methods=['GET'])
def register_page():
    """Render registration page"""
    return render_template('register.html')

# Register Action (POST)
@app.route('/register', methods=['POST'])
def register_action():
    """Handle registration form submission"""
    try:
        data = request.json if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        company_name = data.get('company_name', '').strip()
        
        # Validation
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Username, email and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        logger.info(f"Registration attempt: {username} ({email})")
        
        # Check if MyRDBMS is running
        if not db.health_check():
            logger.error("MyRDBMS is not running")
            return jsonify({
                'success': False, 
                'error': 'Database server is not running. Please start MyRDBMS first.'
            })
        
        # ============================================
        # CRITICAL: Ensure users table exists first!
        # ============================================
        logger.info("Checking if users table exists...")
        
        # First, try to create the database if it doesn't exist
        
        # Check if users table exists
        table_check_query = "SELECT 1 FROM users LIMIT 1"
        table_check_result = db.execute(table_check_query)
        
        # If table doesn't exist (query fails), create it
        if not table_check_result.get('success'):
            logger.info("Users table doesn't exist, creating it...")
            
            # Create users table with proper schema
            create_table_query = """
                CREATE TABLE users (
                    id INT PRIMARY KEY,
                    username VARCHAR(50),
                    email VARCHAR(100),
                    password_hash VARCHAR(255),
                    full_name VARCHAR(100),
                    company_name VARCHAR(100),
                    created_at TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN
                )
            """
            
            create_table_result = db.execute(create_table_query)
            
            if not create_table_result.get('success'):
                logger.error(f"Failed to create users table: {create_table_result.get('error')}")
                
                # Try simpler table creation
                simple_table_query = """
                    CREATE TABLE users (
                        id INT,
                        username VARCHAR(50),
                        email VARCHAR(100),
                        password_hash VARCHAR(255),
                        full_name VARCHAR(100),
                        company_name VARCHAR(100)
                    )
                """
                
                simple_result = db.execute(simple_table_query)
                if not simple_result.get('success'):
                    return jsonify({
                        'success': False, 
                        'error': f'Failed to create users table: {simple_result.get("error")}'
                    }), 500
                
                logger.info("Created simplified users table")
        
        # ============================================
        # Now continue with registration logic
        # ============================================
        
        # Check if user exists
        check_query = f"SELECT id FROM users WHERE email = '{email}' OR username = '{username}'"
        logger.info(f"Checking if user exists: {check_query}")
        check_result = db.execute(check_query)
        
        logger.info(f"Check result: {check_result}")
        
        # Note: In your RDBMS, empty result might still be success
        # We need to check if query executed, not just if data exists
        if not check_result.get('success'):
            # Check if it's an empty result (which is OK) vs actual error
            error_msg = check_result.get('error', '')
            if 'no such table' in error_msg.lower() or 'table' in error_msg.lower():
                # Table might have just been created, try the check again
                logger.info("Table was just created, retrying user check...")
                check_result = db.execute(check_query)
                
                if not check_result.get('success'):
                    error_msg = check_result.get('error', 'Unknown database error')
                    logger.error(f"Database check failed after retry: {error_msg}")
                    return jsonify({'success': False, 'error': f'Database error: {error_msg}'}), 500
            else:
                logger.error(f"Database check failed: {error_msg}")
                return jsonify({'success': False, 'error': f'Database error: {error_msg}'}), 500
        
        # Check if user already exists (has data in result)
        if check_result.get('data') and len(check_result['data']) > 0:
            logger.warning(f"User already exists: {email} or {username}")
            return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
        
        # Hash password
        password_hash = hash_password(password)
        logger.info(f"Password hash created: {password_hash[:30]}...")
        
        # Get next user ID - handle case where table is empty
        id_query = "SELECT MAX(id) as max_id FROM users"
        logger.info(f"Getting max user ID: {id_query}")
        id_result = db.execute(id_query)
        
        logger.info(f"ID result: {id_result}")
        
        if not id_result.get('success'):
            # If we can't query the table, start with ID 1
            user_id = 1
            logger.info(f"Could not get max ID, using default: {user_id}")
        else:
            # Check if we got valid data
            if id_result.get('data') and len(id_result['data']) > 0:
                max_id = id_result['data'][0].get('max_id')
                if max_id is None:
                    user_id = 1
                else:
                    user_id = int(max_id) + 1
            else:
                user_id = 1
            logger.info(f"Calculated user ID: {user_id}")
        
        # Create user using POSITIONAL INSERT syntax
        # Try different INSERT formats until one works
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Try different INSERT approaches
        insert_attempts = [
            # Full INSERT with all columns
            f"INSERT INTO users VALUES ({user_id}, '{username}', '{email}', '{password_hash}', '{full_name}', '{company_name}', '{current_time}', NULL, TRUE)",
            
            # INSERT without timestamps (let DB use defaults)
            f"INSERT INTO users VALUES ({user_id}, '{username}', '{email}', '{password_hash}', '{full_name}', '{company_name}')",
            
            # Minimal INSERT
            f"INSERT INTO users (id, username, email, password_hash) VALUES ({user_id}, '{username}', '{email}', '{password_hash}')"
        ]
        
        create_result = None
        last_error = None
        
        for attempt, insert_query in enumerate(insert_attempts, 1):
            logger.info(f"Insert attempt {attempt}: {insert_query[:80]}...")
            create_result = db.execute(insert_query)
            
            if create_result.get('success'):
                logger.info(f"Insert succeeded on attempt {attempt}")
                break
            else:
                last_error = create_result.get('error')
                logger.warning(f"Insert attempt {attempt} failed: {last_error}")
        
        # Check if any insert worked
        if not create_result or not create_result.get('success'):
            error_msg = last_error or 'Unknown error'
            logger.error(f"All insert attempts failed: {error_msg}")
            
            # Check for duplicate error
            if 'duplicate' in str(error_msg).lower() or 'already exists' in str(error_msg).lower():
                return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
            else:
                return jsonify({'success': False, 'error': f'Registration failed: {error_msg}'}), 500
        
        # Auto-login
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session['full_name'] = full_name
        session['company_name'] = company_name
        
        logger.info(f"Registration successful for user: {username} (ID: {user_id})")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful!',
            'redirect': '/dashboard'
        })
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500
    
# Logout
@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        db.execute(f"DELETE FROM sessions WHERE session_id = '{session_id}'")
    
    response = redirect(url_for('login_page'))
    response.delete_cookie('session_id')
    return response

# Page 2: Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    user = request.user
    user_id = user['user_id']
    
    # Get stats using separate queries (MyRDBMS doesn't support nested SELECT)
    stats = {
        'customer_count': 0,
        'invoice_count': 0,
        'total_outstanding': 0,
        'total_paid': 0
    }
    
    # 1. Customer count
    customer_count_query = f"SELECT COUNT(*) as count FROM customers WHERE user_id = '{user_id}'"
    customer_result = db.execute(customer_count_query)
    if customer_result.get('data'):
        # Extract count - handle different column names
        row = customer_result['data'][0]
        for key, value in row.items():
            if 'count' in key.lower() or isinstance(value, (int, float)):
                stats['customer_count'] = int(value) if value else 0
                break
    
    # 2. Invoice count
    invoice_count_query = f"SELECT COUNT(*) as count FROM invoices WHERE user_id = '{user_id}'"
    invoice_result = db.execute(invoice_count_query)
    if invoice_result.get('data'):
        row = invoice_result['data'][0]
        for key, value in row.items():
            if 'count' in key.lower() or isinstance(value, (int, float)):
                stats['invoice_count'] = int(value) if value else 0
                break
    
    # 3. Total outstanding (invoices not paid)
    outstanding_query = f"""
        SELECT SUM(balance_due) as total 
        FROM invoices 
        WHERE user_id = '{user_id}' AND status != 'paid'
    """
    outstanding_result = db.execute(outstanding_query)
    if outstanding_result.get('data'):
        row = outstanding_result['data'][0]
        for key, value in row.items():
            if 'total' in key.lower() or isinstance(value, (int, float)):
                stats['total_outstanding'] = float(value) if value else 0
                break
    
    # 4. Total paid
    paid_query = f"""
        SELECT SUM(total_amount) as total 
        FROM invoices 
        WHERE user_id = '{user_id}' AND status = 'paid'
    """
    paid_result = db.execute(paid_query)
    if paid_result.get('data'):
        row = paid_result['data'][0]
        for key, value in row.items():
            if 'total' in key.lower() or isinstance(value, (int, float)):
                stats['total_paid'] = float(value) if value else 0
                break
    
    logger.info(f"📊 Dashboard stats: {stats}")
    
    # Get recent invoices
    recent_invoices_query = f"""
        SELECT * FROM invoices i JOIN customers c ON i.customer_id = c.id
    """
    
    recent_result = db.execute(recent_invoices_query)
    recent_invoices = recent_result.get('data', [])
    
    return render_template('dashboard.html', 
                         user=user, 
                         stats=stats,
                         recent_invoices=recent_invoices)

# Page 3: Customers
@app.route('/customers')
@login_required
def customers():
    user_id = request.user['user_id']
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Build query
    where_clause = f"WHERE user_id = {user_id}"
    if search:
        where_clause += f" AND (name LIKE '%{search}%' OR email LIKE '%{search}%')"
    
    # Count total
    count_query = f"SELECT COUNT(*) as total FROM customers {where_clause}"
    count_result = db.execute(count_query)
    #total = count_result['data'][0]['total'] if count_result.get('data') else 0

    # Safer extraction
    if count_result.get('data') and len(count_result['data']) > 0:
        count_row = count_result['data'][0]
        # Try multiple possible keys
        if 'total' in count_row:
            total = count_row['total']
        elif 'count' in count_row:
            total = count_row['count']
        elif 'COUNT(*)' in count_row:
            total = count_row['COUNT(*)']
        else:
            # Use the first value that looks like a number
            for key, value in count_row.items():
                if isinstance(value, (int, float)):
                    total = value
                    break
                elif isinstance(value, str):
                    try:
                        total = int(value)
                        break
                    except:
                        continue
            else:
                total = 0
    else:
        total = 0
    
    # Get paginated customers
    limit = 20
    offset = (page - 1) * limit
    customers_query = f"""
        SELECT * FROM customers 
        {where_clause}
        ORDER BY name
        LIMIT {limit} OFFSET {offset}
    """
    
    customers_result = db.execute(customers_query)
    customers_list = customers_result.get('data', [])
    
    return render_template('customers.html',
                         customers=customers_list,
                         page=page,
                         total=total,
                         search=search)

@app.route('/api/customers', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_customers():
    user_id = request.user['user_id']
    
    if request.method == 'GET':
        # Get all customers for dropdowns
        query = f"""
            SELECT id, name, email FROM customers 
            WHERE user_id = {user_id}
            ORDER BY name
        """
        result = db.execute(query)
        return jsonify(result)
    
    elif request.method == 'POST':

        # Check if customers table exists
        table_check_query = "SELECT 1 FROM customers LIMIT 1"
        table_check_result = db.execute(table_check_query)
        
        # If table doesn't exist (query fails), create it
        if not table_check_result.get('success'):
            logger.info("Customers table doesn't exist, creating it...")
            
            # Create customers table with proper schema
            create_table_query = """
                CREATE TABLE customers (
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
                )
            """
            
            create_table_result = db.execute(create_table_query)
            
            if not create_table_result.get('success'):
                logger.error(f"Failed to create customers table: {create_table_result.get('error')}")
                
        data = request.json
        
        # Get next customer ID
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM customers"
        id_result = db.execute(id_query)
        #customer_id = id_result['data'][0]['next_id'] if id_result.get('data') else 1
        # SAFE extraction with multiple fallbacks
        customer_id = 1
        if id_result.get('data') and len(id_result['data']) > 0:
            row = id_result['data'][0]
            # Try all possible column names
            if 'next_id' in row:
                customer_id = row['next_id']
            elif 'NEXT_ID' in row:
                customer_id = row['NEXT_ID']
            elif 'coalesce(max(id),0)+1' in row:  # Raw column name
                customer_id = row['coalesce(max(id),0)+1']
            else:
                # Use first numeric value found
                for value in row.values():
                    if isinstance(value, (int, float)):
                        customer_id = int(value)
                        break
                    elif isinstance(value, str):
                        try:
                            customer_id = int(value)
                            break
                        except:
                            continue

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Positional INSERT for customers table
        # Columns: id, user_id, name, email, phone, address, city, country, tax_id, notes, created_at, updated_at
        query = f"""
            INSERT INTO customers VALUES (
                {customer_id}, 
                {user_id}, 
                '{data['name']}', 
                '{data.get('email', '')}', 
                '{data.get('phone', '')}', 
                '{data.get('address', '')}', 
                '{data.get('city', '')}', 
                '{data.get('country', '')}',
                '{data.get('tax_id', '')}', 
                '{data.get('notes', '')}', 
                '{current_time}', 
                '{current_time}'
            )
        """
        
        result = db.execute(query)
        return jsonify(result)
    
    elif request.method == 'PUT':
        data = request.json
        customer_id = data['id']
        
        # Verify ownership
        check_query = f"SELECT id FROM customers WHERE id = {customer_id} AND user_id = {user_id}"
        check_result = db.execute(check_query)
        
        if not check_result.get('data'):
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        query = f"""
            UPDATE customers SET
                name = '{data['name']}',
                email = '{data.get('email', '')}',
                phone = '{data.get('phone', '')}',
                address = '{data.get('address', '')}',
                city = '{data.get('city', '')}',
                country = '{data.get('country', '')}',
                tax_id = '{data.get('tax_id', '')}',
                notes = '{data.get('notes', '')}',
                updated_at = '{datetime.now().isoformat()}'
            WHERE id = {customer_id}
        """
        result = db.execute(query)
        return jsonify(result)
    
    elif request.method == 'DELETE':
        customer_id = request.args.get('id')
        
        # Verify ownership
        check_query = f"SELECT id FROM customers WHERE id = {customer_id} AND user_id = {user_id}"
        check_result = db.execute(check_query)
        
        if not check_result.get('data'):
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        query = f"DELETE FROM customers WHERE id = {customer_id}"
        result = db.execute(query)
        return jsonify(result)

# Page 4: Invoices
@app.route('/invoices')
@login_required
def invoices():
    user_id = request.user['user_id']
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    logger.info(f"📄 Invoices page - User ID: {user_id}")
    
    # ============================================
    # Get invoices with SIMPLE query first
    # ============================================
    
    # Simple query to get invoices
    base_where = f"WHERE user_id = '{user_id}'"
    if status:
        base_where += f" AND status = '{status}'"
    
    # First, check if we can do JOINs by testing a simple JOIN
    test_join_query = f"""
        SELECT i.id 
        FROM invoices i 
        JOIN customers c ON i.customer_id = c.id 
        WHERE i.user_id = '{user_id}' 
        LIMIT 1
    """
    test_join_result = db.execute(test_join_query)
    
    invoices_list = []
    total = 0
    
    if test_join_result.get('success') and test_join_result.get('data'):
        logger.info("✅ JOIN queries are supported")
        
        # Build WHERE clause for JOIN queries
        where_clause = f"WHERE i.user_id = '{user_id}'"  # FIX: Added quotes
        if status:
            where_clause += f" AND i.status = '{status}'"
        if search:
            where_clause += f" AND (i.invoice_number LIKE '%{search}%' OR c.name LIKE '%{search}%')"
        
        # Count total
        if search:
            # For search, we need the JOIN
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                {where_clause}
            """
        else:
            # Without search, simple count
            count_query = f"SELECT COUNT(*) as total FROM invoices {base_where}"
        
        count_result = db.execute(count_query)
        logger.info(f"🔍 Count query result: {count_result}")
        
        # Extract total safely
        if count_result.get('data') and len(count_result['data']) > 0:
            count_row = count_result['data'][0]
            for key, value in count_row.items():
                if 'total' in key.lower() or isinstance(value, (int, float)):
                    total = int(value) if value else 0
                    break
        
        # Get paginated invoices - SIMPLIFIED without nested SELECT
        limit = 20
        offset = (page - 1) * limit
        invoices_query = f"""
            SELECT 
                i.*,
                c.name as customer_name,
                c.email as customer_email
                -- Removed: (SELECT COUNT(*) FROM invoice_items WHERE invoice_id = i.id) as item_count
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            {where_clause}
            ORDER BY i.issue_date DESC, i.id DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        logger.info(f"🔍 Invoices query: {invoices_query[:200]}...")
        invoices_result = db.execute(invoices_query)
        invoices_list = invoices_result.get('data', [])
        
        # Get item counts separately if needed
        if invoices_list:
            for invoice in invoices_list:
                invoice_id = invoice.get('id')
                if invoice_id:
                    item_count_query = f"SELECT COUNT(*) as count FROM invoice_items WHERE invoice_id = {invoice_id}"
                    item_result = db.execute(item_count_query)
                    if item_result.get('data'):
                        count_row = item_result['data'][0]
                        for key, value in count_row.items():
                            if 'count' in key.lower():
                                invoice['item_count'] = int(value) if value else 0
                                break
                    else:
                        invoice['item_count'] = 0
                else:
                    invoice['item_count'] = 0
    
    else:
        logger.info("⚠️ JOIN queries not supported, using simple queries")
        
        # Get invoices without JOIN
        simple_query = f"SELECT * FROM invoices {base_where} ORDER BY issue_date DESC LIMIT 20"
        simple_result = db.execute(simple_query)
        invoices_list = simple_result.get('data', [])
        
        # Count total
        count_query = f"SELECT COUNT(*) as total FROM invoices {base_where}"
        count_result = db.execute(count_query)
        if count_result.get('data'):
            count_row = count_result['data'][0]
            for key, value in count_row.items():
                if 'total' in key.lower():
                    total = int(value) if value else 0
                    break
        
        # Get customer info separately
        for invoice in invoices_list:
            customer_id = invoice.get('customer_id')
            if customer_id:
                customer_query = f"SELECT name, email FROM customers WHERE id = {customer_id}"
                customer_result = db.execute(customer_query)
                if customer_result.get('data'):
                    customer = customer_result['data'][0]
                    invoice['customer_name'] = customer.get('name', '')
                    invoice['customer_email'] = customer.get('email', '')
            
            # Get item count
            invoice_id = invoice.get('id')
            if invoice_id:
                item_count_query = f"SELECT COUNT(*) as count FROM invoice_items WHERE invoice_id = {invoice_id}"
                item_result = db.execute(item_count_query)
                if item_result.get('data'):
                    count_row = item_result['data'][0]
                    for key, value in count_row.items():
                        if 'count' in key.lower():
                            invoice['item_count'] = int(value) if value else 0
                            break
    
    logger.info(f"📄 Found {len(invoices_list)} invoices for user {user_id}")
    
    return render_template('invoices.html',
                         invoices=invoices_list,
                         page=page,
                         total=total,
                         status=status,
                         search=search,
                         now=datetime.now)

# Page 5: Invoice Detail
@app.route('/invoice/<int:invoice_id>')
@login_required
def invoice_detail(invoice_id):
    user_id = request.user['user_id']
    
    logger.info(f"📄 Invoice detail - Invoice ID: {invoice_id}, User ID: {user_id}")
    
    # ============================================
    # FIX 2: Get invoice with simple approach
    # ============================================
    
    # First get the invoice
    invoice_query = f"SELECT * FROM invoices WHERE id = {invoice_id} AND user_id = '{user_id}'"
    invoice_result = db.execute(invoice_query)
    
    if not invoice_result.get('data'):
        logger.warning(f"Invoice {invoice_id} not found for user {user_id}")
        return "Invoice not found", 404
    
    invoice = invoice_result['data'][0]
    customer_id = invoice.get('customer_id')
    
    # Get customer info
    customer = {'name': '', 'email': '', 'phone': '', 'address': '', 'city': '', 'country': '', 'tax_id': ''}
    if customer_id:
        customer_query = f"SELECT name, email, phone, address, city, country, tax_id FROM customers WHERE id = {customer_id}"
        customer_result = db.execute(customer_query)
        if customer_result.get('data'):
            customer = customer_result['data'][0]
    
    # Merge customer info into invoice
    invoice['customer_name'] = customer.get('name', '')
    invoice['customer_email'] = customer.get('email', '')
    invoice['customer_phone'] = customer.get('phone', '')
    invoice['customer_address'] = customer.get('address', '')
    invoice['customer_city'] = customer.get('city', '')
    invoice['customer_country'] = customer.get('country', '')
    invoice['customer_tax_id'] = customer.get('tax_id', '')
    
    # Get invoice items
    items_query = f"SELECT * FROM invoice_items WHERE invoice_id = {invoice_id} ORDER BY id"
    items_result = db.execute(items_query)
    items = items_result.get('data', [])
    
    # Get payments
    payments_query = f"SELECT * FROM payments WHERE invoice_id = {invoice_id} ORDER BY payment_date DESC"
    payments_result = db.execute(payments_query)
    payments = payments_result.get('data', [])
    
    logger.info(f"📄 Invoice {invoice_id} - Items: {len(items)}, Payments: {len(payments)}")
    
    return render_template('invoice_detail.html',
                         invoice=invoice,
                         items=items,
                         payments=payments)

# Page 6: Payments
@app.route('/payments')
@login_required
def payments():
    user_id = request.user['user_id']
    page = request.args.get('page', 1, type=int)
    
    # Get payments with invoice and customer info
    limit = 20
    offset = (page - 1) * limit
    payments_query = f"""
        SELECT 
            p.*,
            i.invoice_number,
            i.total_amount,
            i.balance_due,
            c.name as customer_name
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.id
        JOIN customers c ON i.customer_id = c.id
        WHERE i.user_id = {user_id}
        ORDER BY p.payment_date DESC
        LIMIT {limit} OFFSET {offset}
    """
    
    payments_result = db.execute(payments_query)
    payments_list = payments_result.get('data', [])
    
    # Count total
    count_query = f"""
        SELECT COUNT(*) as total 
        FROM payments p
        JOIN invoices i ON p.invoice_id = i.id
        WHERE i.user_id = {user_id}
    """
    count_result = db.execute(count_query)
    total = count_result['data'][0]['total'] if count_result.get('data') else 0
    
    return render_template('payments.html',
                         payments=payments_list,
                         page=page,
                         total=total)

# API endpoints for invoice operations
@app.route('/api/invoices', methods=['POST'])
@login_required
def create_invoice():
    try:
        user_id = request.user['user_id']
        data = request.json
        
        logger.info(f"📝 Creating invoice for user {user_id}")
        logger.info(f"📝 Invoice data: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if 'customer_id' not in data:
            return jsonify({'success': False, 'error': 'Customer ID is required'}), 400
        
        if 'items' not in data or not data['items']:
            return jsonify({'success': False, 'error': 'At least one item is required'}), 400
        
        # ============================================
        # 1. ENSURE TABLES EXIST
        # ============================================
        
        # Check/create invoices table
        invoices_table_check = "SELECT 1 FROM invoices LIMIT 1"
        invoices_table_result = db.execute(invoices_table_check)
        
        if not invoices_table_result.get('success'):
            logger.info("Creating invoices table...")
            create_invoices_table = """
                CREATE TABLE invoices (
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
                )
            """
            create_result = db.execute(create_invoices_table)
            if not create_result.get('success'):
                logger.error(f"Failed to create invoices table: {create_result.get('error')}")
                return jsonify({'success': False, 'error': f'Failed to create invoices table: {create_result.get("error")}'}), 500
        
        # Check/create invoice_items table
        items_table_check = "SELECT 1 FROM invoice_items LIMIT 1"
        items_table_result = db.execute(items_table_check)
        
        if not items_table_result.get('success'):
            logger.info("Creating invoice_items table...")
            create_items_table = """
                CREATE TABLE invoice_items (
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
                )
            """
            create_result = db.execute(create_items_table)
            if not create_result.get('success'):
                logger.error(f"Failed to create invoice_items table: {create_result.get('error')}")
                return jsonify({'success': False, 'error': f'Failed to create invoice_items table: {create_result.get("error")}'}), 500
        
        # ============================================
        # 2. GENERATE INVOICE NUMBER
        # ============================================
        
        today = datetime.now().strftime('%Y%m%d')
        number_query = f"SELECT COUNT(*) as count FROM invoices WHERE invoice_number LIKE 'INV-{today}-%'"
        number_result = db.execute(number_query)
        
        count = 0
        if number_result.get('data') and len(number_result['data']) > 0:
            count_row = number_result['data'][0]
            # Extract count from any key that contains 'count'
            for key, value in count_row.items():
                if 'count' in key.lower() or isinstance(value, (int, float)):
                    count = int(value) if value else 0
                    break
        
        invoice_number = f"INV-{today}-{count + 1:04d}"
        logger.info(f"Generated invoice number: {invoice_number}")
        
        # ============================================
        # 3. GET NEXT INVOICE ID
        # ============================================
        
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM invoices"
        id_result = db.execute(id_query)
        
        invoice_id = 1  # Default
        if id_result.get('data') and len(id_result['data']) > 0:
            id_row = id_result['data'][0]
            # Extract next_id from any numeric value
            for key, value in id_row.items():
                if 'next_id' in key.lower() or isinstance(value, (int, float)):
                    try:
                        invoice_id = int(value) if value else 1
                        break
                    except:
                        continue
        
        logger.info(f"Next invoice ID: {invoice_id}")
        
        # ============================================
        # 4. CALCULATE TOTALS
        # ============================================
        
        subtotal = 0
        tax_amount = 0
        
        for item in data['items']:
            quantity = float(item.get('quantity', 0))
            unit_price = float(item.get('unit_price', 0))
            tax_rate = float(item.get('tax_rate', 0))
            
            item_subtotal = quantity * unit_price
            item_tax = item_subtotal * (tax_rate / 100)
            
            subtotal += item_subtotal
            tax_amount += item_tax
        
        total_amount = subtotal + tax_amount
        balance_due = total_amount  # Initially balance due equals total amount
        
        logger.info(f"Calculated totals - Subtotal: {subtotal}, Tax: {tax_amount}, Total: {total_amount}")
        
        # ============================================
        # 5. CREATE INVOICE
        # ============================================
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        invoice_query = f"""
            INSERT INTO invoices VALUES (
                {invoice_id}, 
                {int(data['customer_id'])}, 
                {user_id}, 
                '{invoice_number}',
                '{data['issue_date']}', 
                '{data['due_date']}', 
                {subtotal}, 
                {tax_amount},
                {total_amount}, 
                0,  -- amount_paid starts at 0
                {total_amount},  -- balance_due starts at total_amount
                '{data.get('status', 'draft')}', 
                '{data.get('currency', 'KES')}',
                '{data.get('notes', '').replace("'", "''")}', 
                '{data.get('terms', '').replace("'", "''")}',
                '{current_time}', 
                '{current_time}'
            )
        """
        
        logger.info(f"Invoice insert query: {invoice_query[:200]}...")
        invoice_result = db.execute(invoice_query)
        
        if not invoice_result.get('success'):
            logger.error(f"Failed to create invoice: {invoice_result.get('error')}")
            return jsonify({
                'success': False,
                'error': f'Failed to create invoice: {invoice_result.get("error")}'
            }), 500
        
        # ============================================
        # 6. ADD INVOICE ITEMS
        # ============================================
        
        # Get next item ID
        item_id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM invoice_items"
        item_id_result = db.execute(item_id_query)
        
        item_start_id = 1
        if item_id_result.get('data') and len(item_id_result['data']) > 0:
            id_row = item_id_result['data'][0]
            for key, value in id_row.items():
                if 'next_id' in key.lower() or isinstance(value, (int, float)):
                    try:
                        item_start_id = int(value) if value else 1
                        break
                    except:
                        continue
        
        item_errors = []
        for idx, item in enumerate(data['items']):
            item_id = item_start_id + idx
            
            item_query = f"""
                INSERT INTO invoice_items VALUES (
                    {item_id}, 
                    {invoice_id}, 
                    '{item['description'].replace("'", "''")}', 
                    {float(item['quantity'])}, 
                    {float(item['unit_price'])}, 
                    {float(item.get('tax_rate', 0))}, 
                    '{current_time}'
                )
            """
            
            item_result = db.execute(item_query)
            if not item_result.get('success'):
                item_errors.append(f"Item {idx + 1}: {item_result.get('error')}")
                logger.error(f"Failed to insert item {idx + 1}: {item_result.get('error')}")
        
        if item_errors:
            logger.warning(f"Some items failed: {item_errors}")
            # Continue anyway - invoice was created
        
        logger.info(f"✅ Invoice created successfully: {invoice_number} (ID: {invoice_id})")
        
        return jsonify({
            'success': True,
            'message': 'Invoice created successfully',
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'total_amount': total_amount,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'item_errors': item_errors if item_errors else None
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating invoice: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
    
@app.route('/api/invoices/<int:invoice_id>/pay', methods=['POST'])
@login_required
def record_payment(invoice_id):
    user_id = request.user['user_id']
    data = request.json
    
    # Verify invoice ownership
    check_query = f"SELECT id FROM invoices WHERE id = {invoice_id} AND user_id = {user_id}"
    check_result = db.execute(check_query)
    
    if not check_result.get('data'):
        return jsonify({'success': False, 'error': 'Invoice not found'}), 404
    
    # Get next payment ID
    id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM payments"
    id_result = db.execute(id_query)
    payment_id = id_result['data'][0]['next_id'] if id_result.get('data') else 1
    
    # Create payment
    payment_query = f"""
        INSERT INTO payments (
            id, invoice_id, amount, payment_method, reference_number, payment_date, notes
        ) VALUES (
            {payment_id}, {invoice_id}, {data['amount']}, '{data['payment_method']}',
            '{data.get('reference_number', '')}', '{data['payment_date']}', 
            '{data.get('notes', '')}'
        )
    """
    
    payment_result = db.execute(payment_query)
    if not payment_result.get('success'):
        return jsonify(payment_result), 500
    
    # Update invoice amount_paid
    update_query = f"""
        UPDATE invoices 
        SET amount_paid = amount_paid + {data['amount']},
            status = CASE 
                WHEN total_amount <= amount_paid + {data['amount']} THEN 'paid'
                ELSE status 
            END,
            updated_at = '{datetime.now().isoformat()}'
        WHERE id = {invoice_id}
    """
    
    db.execute(update_query)
    
    return jsonify({'success': True, 'payment_id': payment_id})

# Health check endpoint
@app.route('/health')
def health():
    db_healthy = db.health_check()
    return jsonify({
        'status': 'healthy' if db_healthy else 'unhealthy',
        'database': 'connected' if db_healthy else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Server Error: {error}')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Check database connection
    if db.health_check():
        logger.info("Database connection successful")
    else:
        logger.warning("Cannot connect to database")
    
    app.run(debug=True, port=8000, host='0.0.0.0')