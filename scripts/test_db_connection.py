#!/usr/bin/env python3
"""
Database connection test script
"""
import os

import psycopg2
from psycopg2 import OperationalError

from app.database import db
from app.main import create_app


def test_direct_connection():
    """Test direct PostgreSQL connection"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False

    try:
        print(f"Testing connection to: {database_url.split('@')[1]}")  # Hide password
        conn = psycopg2.connect(database_url)

        # Test simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print("SUCCESS: Database connection established")
        print(f"PostgreSQL version: {version[0]}")

        # Test if deployment_log table exists
        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'deployment_log';
        """
        )
        table_exists = cursor.fetchone()

        if table_exists:
            print("SUCCESS: deployment_log table exists")

            # Count records
            cursor.execute("SELECT COUNT(*) FROM deployment_log;")
            count = cursor.fetchone()[0]
            print(f"INFO: deployment_log has {count} records")
        else:
            print("WARNING: deployment_log table does not exist")

        cursor.close()
        conn.close()
        return True

    except OperationalError as e:
        print(f"ERROR: Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False


def test_app_connection():
    """Test database connection through Flask app"""
    try:
        app = create_app(testing=False)

        with app.app_context():
            # Test database connection
            db.session.execute("SELECT 1")
            print("SUCCESS: Flask app database connection working")

            # Test if model works
            from app.models import DeploymentLog

            count = DeploymentLog.query.count()
            print(f"SUCCESS: DeploymentLog model working, {count} records found")

            return True

    except Exception as e:
        print(f"ERROR: Flask app database connection failed: {e}")
        return False


def test_render_connection():
    """Test connection to Render database specifically"""
    # Common Render PostgreSQL connection patterns
    render_patterns = [
        "postgresql://",
        "postgres://",
    ]

    database_url = os.getenv("DATABASE_URL", "")

    if not any(pattern in database_url for pattern in render_patterns):
        print("ERROR: DATABASE_URL doesn't look like a PostgreSQL connection string")
        return False

    # Extract host for debugging
    try:
        if "@" in database_url:
            host_part = database_url.split("@")[1].split("/")[0]
            print(f"INFO: Connecting to host: {host_part}")

        return test_direct_connection()

    except Exception as e:
        print(f"ERROR: Could not parse connection string: {e}")
        return False


if __name__ == "__main__":
    print("=== Database Connection Test ===\n")

    print("1. Testing direct PostgreSQL connection...")
    direct_success = test_direct_connection()

    print("\n2. Testing Flask app connection...")
    app_success = test_app_connection()

    print("\n=== Test Results ===")
    print(f"Direct connection: {'PASS' if direct_success else 'FAIL'}")
    print(f"App connection: {'PASS' if app_success else 'FAIL'}")

    if direct_success and app_success:
        print("\nSUCCESS: All database connections working!")
    else:
        print("\nFAILURE: Some database connections failed.")
        print("Check your DATABASE_URL environment variable.")
