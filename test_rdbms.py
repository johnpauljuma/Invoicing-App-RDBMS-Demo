# test_rdbms.py
import requests
import hashlib

def test_insert_syntax():
    """Test the correct INSERT syntax for your RDBMS"""
    
    base_url = "http://localhost:5000/api"
    db_name = "invoicing_db"
    
    # Test simple INSERT
    test_query = "INSERT INTO users VALUES (999, 'testuser', 'test@example.com', 'hash123', 'Test User', 'Test Company', '2024-01-01', NULL, TRUE)"
    
    try:
        response = requests.post(
            f"{base_url}/databases/{db_name}/execute",
            json={'query': test_query},
            timeout=10
        )
        
        result = response.json()
        print(f"Test INSERT result: {result}")
        
        # Now try to select the test user
        select_query = "SELECT * FROM users WHERE id = 999"
        response = requests.post(
            f"{base_url}/databases/{db_name}/execute",
            json={'query': select_query},
            timeout=10
        )
        
        select_result = response.json()
        print(f"Test SELECT result: {select_result}")
        
        # Clean up
        delete_query = "DELETE FROM users WHERE id = 999"
        response = requests.post(
            f"{base_url}/databases/{db_name}/execute",
            json={'query': delete_query},
            timeout=10
        )
        
        return True
        
    except Exception as e:
        print(f"Error testing RDBMS: {e}")
        return False

def test_password_hash():
    """Test password hashing matches demo user"""
    password = "demo123"
    hash_obj = hashlib.sha256(password.encode())
    hash_digest = hash_obj.hexdigest()
    
    print(f"\nPassword: {password}")
    print(f"SHA-256 hash: {hash_digest}")
    print(f"Demo user hash: d3ad9315b7be5dd53b31a273b3b3aba5defe700808305aa16a3062b76658a791")
    print(f"Match: {hash_digest == 'd3ad9315b7be5dd53b31a273b3b3aba5defe700808305aa16a3062b76658a791'}")
    
    return hash_digest

if __name__ == "__main__":
    print("=== Testing RDBMS INSERT Syntax ===")
    test_insert_syntax()
    
    print("\n=== Testing Password Hash ===")
    test_password_hash()