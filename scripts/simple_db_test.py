#!/usr/bin/env python3
"""
Simple database connection test without app dependencies
"""
import os
import psycopg2
from psycopg2 import OperationalError

def test_database_connection():
    """Test PostgreSQL database connection"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        print(f"Testing connection to database...")
        # Hide password in output
        safe_url = database_url.split('@')[0].split(':')[-1][:4] + '***' + '@' + database_url.split('@')[1]
        print(f"Connection string: {safe_url}")
        
        conn = psycopg2.connect(database_url)
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("SUCCESS: Database connection established")
        print(f"PostgreSQL version: {version[0][:50]}...")
        
        # Test if deployment_log table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'deployment_log';
        """)
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("SUCCESS: deployment_log table exists")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM deployment_log;")
            count = cursor.fetchone()[0]
            print(f"INFO: deployment_log has {count} records")
            
            # Show recent records if any
            if count > 0:
                cursor.execute("SELECT version, environment, status, deployed_at FROM deployment_log ORDER BY deployed_at DESC LIMIT 3;")
                records = cursor.fetchall()
                print("Recent deployments:")
                for record in records:
                    print(f"  - {record[0]} to {record[1]} ({record[2]}) at {record[3]}")
        else:
            print("INFO: deployment_log table does not exist - will be created on first app run")
        
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        print(f"ERROR: Database connection failed: {e}")
        print("Common issues:")
        print("  - Wrong password")
        print("  - Wrong host or port")
        print("  - Database doesn't exist")
        print("  - Network connectivity issues")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== Database Connection Test ===\n")
    success = test_database_connection()
    
    print(f"\n=== Result ===")
    if success:
        print("SUCCESS: Database connection is working!")
        print("Your Render web service should be able to connect.")
    else:
        print("FAILURE: Database connection failed.")
        print("Check your DATABASE_URL in Render environment variables.")
