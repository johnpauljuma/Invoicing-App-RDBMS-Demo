#!/bin/bash
# deploy.sh

echo "🚀 Deploying Invoicing App..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask app
echo "🌐 Starting Flask app..."
python3 app.py

# Run the init.sql script
python3 -c "
import requests
with open('database/init.sql', 'r') as f:
    sql_script = f.read()

# Split by semicolon and execute each query
queries = [q.strip() for q in sql_script.split(';') if q.strip()]

for query in queries:
    response = requests.post('http://localhost:5000/api/databases/invoicing_db/execute',
                           json={'query': query})
    print(f'Executed: {query[:50]}... -> {response.status_code}')
"