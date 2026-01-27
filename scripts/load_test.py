# scripts/load_test.py
from locust import HttpUser, task, between
import random

class CICDUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def visit_homepage(self):
        self.client.get("/")
    
    @task(2)
    def check_health(self):
        self.client.get("/health")
    
    @task(1)
    def get_deployments(self):
        self.client.get("/api/deployments")
    
    @task(1)
    def create_deployment(self):
        versions = ["1.0.0", "1.0.1", "1.1.0", "2.0.0"]
        statuses = ["success", "failed", "pending"]
        self.client.post("/api/deployments", json={
            "version": random.choice(versions),
            "status": random.choice(statuses),
            "user": f"user{random.randint(1, 100)}",
            "commit_hash": f"abc{random.randint(100, 999)}",
            "environment": random.choice(["staging", "production"])
        })