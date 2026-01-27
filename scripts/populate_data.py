#!/usr/bin/env python3
"""
Script to populate sample deployment data for testing
"""
import requests
import random
from datetime import datetime, timedelta
import time

def create_sample_deployment(base_url, environment):
    """Create a sample deployment"""
    versions = ["1.0.0", "1.0.1", "1.1.0", "1.1.1", "1.2.0", "2.0.0", "2.0.1", "2.1.0"]
    
    deployment_data = {
        "version": random.choice(versions),
        "environment": environment
    }
    
    try:
        response = requests.post(f"{base_url}/api/deployments", json=deployment_data, timeout=10)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Created deployment: {result['version']} to {result['environment']}")
            return True
        else:
            print(f"❌ Failed to create deployment: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating deployment: {e}")
        return False

def populate_environment(base_url, environment, count=10):
    """Populate an environment with sample deployments"""
    print(f"\n🔧 Populating {environment} environment with {count} deployments...")
    
    success_count = 0
    for i in range(count):
        if create_sample_deployment(base_url, environment):
            success_count += 1
        time.sleep(0.5)  # Small delay between requests
    
    print(f"✅ Successfully created {success_count}/{count} deployments for {environment}")
    return success_count

def check_application_health(base_url, environment_name):
    """Check if application is healthy"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            db_status = "healthy" in health_data.get("database", "")
            print(f"✅ {environment_name} is UP")
            print(f"   Database: {health_data.get('database', 'unknown')}")
            print(f"   Environment: {health_data.get('environment', 'unknown')}")
            return db_status
        else:
            print(f"❌ {environment_name} health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {environment_name} is not accessible: {e}")
        return False

def main():
    """Main function to populate data"""
    print("=== CI/CD Demo Data Population ===\n")
    
    # Environment URLs
    staging_url = "https://cicd-demo-staging-1s8u.onrender.com"
    production_url = "https://cicd-demo-e71o.onrender.com"
    
    # Check health first
    print("1. Checking application health...")
    staging_healthy = check_application_health(staging_url, "Staging")
    production_healthy = check_application_health(production_url, "Production")
    
    if not staging_healthy and not production_healthy:
        print("\n❌ Both environments are unhealthy. Please check the applications.")
        return
    
    # Populate staging
    if staging_healthy:
        print(f"\n2. Populating staging environment...")
        populate_environment(staging_url, "staging", count=8)
    
    # Populate production
    if production_healthy:
        print(f"\n3. Populating production environment...")
        populate_environment(production_url, "production", count=12)
    
    # Wait a moment for data to be processed
    print(f"\n4. Waiting for data processing...")
    time.sleep(3)
    
    # Verify data
    print(f"\n5. Verifying data...")
    
    if staging_healthy:
        try:
            response = requests.get(f"{staging_url}/api/deployments", timeout=10)
            if response.status_code == 200:
                data = response.json()
                staging_count = len(data.get("deployments", []))
                print(f"✅ Staging has {staging_count} deployments")
        except Exception as e:
            print(f"❌ Error checking staging data: {e}")
    
    if production_healthy:
        try:
            response = requests.get(f"{production_url}/api/deployments", timeout=10)
            if response.status_code == 200:
                data = response.json()
                production_count = len(data.get("deployments", []))
                print(f"✅ Production has {production_count} deployments")
        except Exception as e:
            print(f"❌ Error checking production data: {e}")
    
    print(f"\n=== Data Population Complete ===")
    print(f"You can now visit your dashboards:")
    print(f"Staging: {staging_url}")
    print(f"Production: {production_url}")

if __name__ == "__main__":
    main()
