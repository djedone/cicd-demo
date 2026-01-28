#!/usr/bin/env python3
"""
Data migration script to properly separate staging and production data
"""
import os
from datetime import datetime

import psycopg2
from psycopg2 import OperationalError


def get_database_connection():
    """Get database connection from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)


def migrate_existing_data():
    """Migrate existing data to proper environment separation"""
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        print("=== Data Migration for Environment Separation ===\n")

        # Check current data state
        cursor.execute("SELECT COUNT(*) FROM deployment_log;")
        total_count = cursor.fetchone()[0]
        print(f"Total deployments in database: {total_count}")

        if total_count == 0:
            print("No data to migrate. Database is empty.")
            return

        # Check environment distribution
        cursor.execute(
            """
            SELECT environment, COUNT(*) 
            FROM deployment_log 
            GROUP BY environment 
            ORDER BY environment;
        """
        )
        env_distribution = cursor.fetchall()

        print("\nCurrent environment distribution:")
        for env, count in env_distribution:
            print(f"  {env}: {count} deployments")

        # Migrate data without environment set
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM deployment_log 
            WHERE environment IS NULL OR environment = '';
        """
        )
        null_env_count = cursor.fetchone()[0]

        if null_env_count > 0:
            print(f"\nFound {null_env_count} deployments without environment setting")

            # Assign environment based on deployment time pattern
            # Older deployments -> production, newer -> staging
            cursor.execute(
                """
                UPDATE deployment_log 
                SET environment = 'production'
                WHERE environment IS NULL OR environment = ''
                AND deployed_at < NOW() - INTERVAL '1 hour';
            """
            )

            cursor.execute(
                """
                UPDATE deployment_log 
                SET environment = 'staging'
                WHERE environment IS NULL OR environment = '';
            """
            )

            print(f"Migrated {null_env_count} deployments to proper environments")

        # Verify migration
        cursor.execute(
            """
            SELECT environment, COUNT(*) 
            FROM deployment_log 
            GROUP BY environment 
            ORDER BY environment;
        """
        )
        new_distribution = cursor.fetchall()

        print("\nNew environment distribution after migration:")
        for env, count in new_distribution:
            print(f"  {env}: {count} deployments")

        # Create sample data if needed
        if total_count < 5:
            print("\nAdding sample data for testing...")
            add_sample_data(cursor)

        conn.commit()
        print("\n✅ Data migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def add_sample_data(cursor):
    """Add sample data for testing environment separation"""
    sample_deployments = [
        ("1.0.0", "production", "2024-01-20 10:00:00"),
        ("1.0.1", "production", "2024-01-21 14:30:00"),
        ("1.1.0", "production", "2024-01-22 09:15:00"),
        ("1.1.0", "staging", "2024-01-22 11:00:00"),
        ("1.1.1", "staging", "2024-01-23 16:45:00"),
    ]

    for version, environment, deployed_at in sample_deployments:
        cursor.execute(
            """
            INSERT INTO deployment_log (version, environment, status, deployed_at)
            VALUES (%s, %s, 'success', %s)
            ON CONFLICT DO NOTHING;
        """,
            (version, environment, deployed_at),
        )

    print("Added 5 sample deployments for testing")


def verify_data_separation():
    """Verify that data separation is working correctly"""
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        print("\n=== Verifying Data Separation ===\n")

        # Test staging filter
        cursor.execute(
            """
            SELECT COUNT(*) FROM deployment_log WHERE environment = 'staging';
        """
        )
        staging_count = cursor.fetchone()[0]

        # Test production filter
        cursor.execute(
            """
            SELECT COUNT(*) FROM deployment_log WHERE environment = 'production';
        """
        )
        production_count = cursor.fetchone()[0]

        print(f"Staging deployments: {staging_count}")
        print(f"Production deployments: {production_count}")

        # Test recent deployments by environment
        cursor.execute(
            """
            SELECT environment, version, deployed_at
            FROM deployment_log
            WHERE environment IN ('staging', 'production')
            ORDER BY deployed_at DESC
            LIMIT 5;
        """
        )
        recent = cursor.fetchall()

        print("\nRecent deployments by environment:")
        for env, version, deployed_at in recent:
            print(f"  {env}: {version} at {deployed_at}")

        print("\n✅ Data separation verification completed!")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        migrate_existing_data()
        verify_data_separation()
    except Exception as e:
        print(f"❌ Script failed: {e}")
        exit(1)
