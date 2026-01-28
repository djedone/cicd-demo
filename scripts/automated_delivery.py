#!/usr/bin/env python3
"""
Automated delivery script for CI/CD pipeline
Integrates all changes to codebase with automated delivery
"""
import json
import os
import subprocess
import sys
from datetime import datetime

import requests


class AutomatedDelivery:
    def __init__(self):
        self.staging_url = os.getenv(
            "STAGING_URL", "https://cicd-demo-staging-1s8u.onrender.com"
        )
        self.production_url = os.getenv(
            "PRODUCTION_URL", "https://cicd-demo-e71o.onrender.com"
        )
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "djedone")
        self.repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "cicd-demo")

    def run_command(self, command, check=True):
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=check
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {command}")
            print(f"Error: {e.stderr}")
            if check:
                raise
            return e.stdout.strip(), e.stderr.strip()

    def verify_codebase_integrity(self):
        """Verify codebase integrity before delivery"""
        print("=== Verifying Codebase Integrity ===")

        # Check if working directory is clean
        stdout, stderr = self.run_command("git status --porcelain")
        if stdout:
            print("❌ Working directory is not clean")
            print("Uncommitted changes:")
            print(stdout)
            return False

        print("✅ Working directory is clean")

        # Run tests
        print("Running tests...")
        stdout, stderr = self.run_command("python -m pytest tests/ -v", check=False)
        if "FAILED" in stdout or "ERROR" in stdout:
            print("❌ Tests failed")
            print(stdout)
            return False

        print("✅ All tests passed")

        # Run linter checks
        print("Running linter checks...")
        stdout, stderr = self.run_command("flake8 app/ tests/ scripts/", check=False)
        if stdout and "error" in stdout.lower():
            print("❌ Linter checks failed")
            print(stdout)
            return False

        print("✅ Linter checks passed")

        return True

    def check_environment_health(self, url, environment_name):
        """Check if environment is healthy"""
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                db_healthy = "healthy" in health_data.get("database", "")
                print(f"✅ {environment_name} is healthy")
                print(f"   Database: {health_data.get('database', 'unknown')}")
                return db_healthy
            else:
                print(
                    f"❌ {environment_name} health check failed: {response.status_code}"
                )
                return False
        except Exception as e:
            print(f"❌ {environment_name} is not accessible: {e}")
            return False

    def create_deployment_record(self, url, version, environment):
        """Create deployment record"""
        deployment_data = {"version": version, "environment": environment}

        try:
            response = requests.post(
                f"{url}/api/deployments", json=deployment_data, timeout=10
            )
            if response.status_code == 201:
                result = response.json()
                print(
                    f"✅ Deployment recorded: {result['version']} to {result['environment']}"
                )
                return True
            else:
                print(f"❌ Failed to record deployment: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Error recording deployment: {e}")
            return False

    def run_integration_tests(self, url, environment_name):
        """Run integration tests against deployed environment"""
        print(f"Running integration tests against {environment_name}...")

        test_cases = [
            ("GET", "/health", 200),
            ("GET", "/api/deployments", 200),
            ("GET", "/api/stats", 200),
            ("GET", "/api/metrics/custom", 200),
        ]

        passed = 0
        total = len(test_cases)

        for method, endpoint, expected_status in test_cases:
            try:
                if method == "GET":
                    response = requests.get(f"{url}{endpoint}", timeout=10)

                if response.status_code == expected_status:
                    passed += 1
                    print(f"  ✅ {method} {endpoint} - {response.status_code}")
                else:
                    print(
                        f"  ❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}"
                    )
            except Exception as e:
                print(f"  ❌ {method} {endpoint} - Error: {e}")

        success_rate = (passed / total) * 100
        print(f"Integration tests: {passed}/{total} passed ({success_rate:.1f}%)")

        return success_rate >= 80  # Require at least 80% pass rate

    def create_github_deployment(self, environment, sha, ref):
        """Create GitHub deployment status"""
        if not self.github_token:
            print("⚠️  No GitHub token provided, skipping GitHub deployment status")
            return True

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/deployments"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        deployment_data = {
            "ref": ref,
            "environment": environment,
            "description": f"Automated deployment to {environment}",
        }

        try:
            response = requests.post(url, json=deployment_data, headers=headers)
            if response.status_code == 201:
                deployment = response.json()
                deployment_url = deployment["url"]

                # Update deployment status
                status_data = {
                    "state": "success",
                    "description": f"Deployment to {environment} completed successfully",
                }

                status_response = requests.post(
                    f"{deployment_url}/statuses", json=status_data, headers=headers
                )
                if status_response.status_code == 201:
                    print(f"✅ GitHub deployment status updated for {environment}")
                    return True
                else:
                    print(f"❌ Failed to update GitHub deployment status")
                    return False
            else:
                print(f"❌ Failed to create GitHub deployment: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error creating GitHub deployment: {e}")
            return False

    def deliver_to_staging(self):
        """Deliver to staging environment"""
        print("\n=== Delivering to Staging ===")

        # Get current commit info
        stdout, _ = self.run_command("git rev-parse HEAD")
        commit_sha = stdout

        stdout, _ = self.run_command("git rev-parse --abbrev-ref HEAD")
        branch = stdout

        # Check staging health
        if not self.check_environment_health(self.staging_url, "Staging"):
            print("❌ Staging environment is not healthy")
            return False

        # Create deployment record
        version = f"staging-{commit_sha[:8]}"
        if not self.create_deployment_record(self.staging_url, version, "staging"):
            return False

        # Run integration tests
        if not self.run_integration_tests(self.staging_url, "Staging"):
            print("❌ Staging integration tests failed")
            return False

        # Create GitHub deployment status
        self.create_github_deployment("staging", commit_sha, branch)

        print("✅ Staging delivery completed successfully")
        return True

    def deliver_to_production(self):
        """Deliver to production environment"""
        print("\n=== Delivering to Production ===")

        # Get current commit info
        stdout, _ = self.run_command("git rev-parse HEAD")
        commit_sha = stdout

        stdout, _ = self.run_command("git rev-parse --abbrev-ref HEAD")
        branch = stdout

        # Check production health
        if not self.check_environment_health(self.production_url, "Production"):
            print("❌ Production environment is not healthy")
            return False

        # Create deployment record
        version = f"v{commit_sha[:8]}"
        if not self.create_deployment_record(
            self.production_url, version, "production"
        ):
            return False

        # Run integration tests
        if not self.run_integration_tests(self.production_url, "Production"):
            print("❌ Production integration tests failed")
            return False

        # Create GitHub deployment status
        self.create_github_deployment("production", commit_sha, branch)

        print("✅ Production delivery completed successfully")
        return True

    def rollback_deployment(self, environment):
        """Rollback deployment to previous version"""
        print(f"\n=== Rolling back {environment} ===")

        url = self.staging_url if environment == "staging" else self.production_url

        try:
            # Get recent deployments
            response = requests.get(f"{url}/api/deployments", timeout=10)
            if response.status_code == 200:
                deployments = response.json().get("deployments", [])

                if len(deployments) < 2:
                    print("❌ No previous deployment to rollback to")
                    return False

                # Get previous deployment (skip the latest one)
                previous_deployment = deployments[1]
                rollback_version = f"rollback-{previous_deployment['version']}"

                # Create rollback deployment record
                rollback_data = {
                    "version": rollback_version,
                    "environment": environment,
                }

                response = requests.post(
                    f"{url}/api/deployments", json=rollback_data, timeout=10
                )
                if response.status_code == 201:
                    print(f"✅ Rollback completed: {rollback_version}")
                    return True
                else:
                    print(f"❌ Rollback failed: {response.status_code}")
                    return False
            else:
                print(f"❌ Failed to get deployments: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during rollback: {e}")
            return False

    def run_delivery_pipeline(self, target_environment="both"):
        """Run complete automated delivery pipeline"""
        print("=== Automated Delivery Pipeline ===")
        print(f"Target environment: {target_environment}")
        print(f"Started at: {datetime.now().isoformat()}")

        # Step 1: Verify codebase integrity
        if not self.verify_codebase_integrity():
            print("❌ Codebase integrity check failed")
            return False

        # Step 2: Deliver to target environments
        success = True

        if target_environment in ["staging", "both"]:
            if not self.deliver_to_staging():
                success = False

        if target_environment in ["production", "both"]:
            if not self.deliver_to_production():
                success = False

        # Step 3: Summary
        print(f"\n=== Delivery Pipeline Summary ===")
        print(f"Completed at: {datetime.now().isoformat()}")
        print(f"Status: {'✅ Success' if success else '❌ Failed'}")

        return success


def main():
    """Main function"""
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = os.getenv("TARGET_ENVIRONMENT", "both")

    if target not in ["staging", "production", "both"]:
        print("Invalid target environment. Use: staging, production, or both")
        sys.exit(1)

    delivery = AutomatedDelivery()

    try:
        success = delivery.run_delivery_pipeline(target)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Delivery pipeline interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Delivery pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
