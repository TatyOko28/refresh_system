# File: tests/performance/test_performance.py
import pytest
from locust import HttpUser, task, between
from django.urls import reverse
from apps.authentication.models import User
from apps.referrals.models import ReferralCode
from datetime import datetime, timedelta
import pytz

class ReferralSystemUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login/", {
            "email": "test@example.com",
            "password": "testpass123"
        })
        self.token = response.json()['tokens']['access']
    
    @task
    def get_referral_code(self):
        self.client.get(
            "/api/v1/referrals/codes/by-email/test@example.com/",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task
    def create_referral_code(self):
        self.client.post(
            "/api/v1/referrals/codes/create/",
            json={"expires_at": (datetime.now(pytz.UTC) + timedelta(days=7)).isoformat()},
            headers={"Authorization": f"Bearer {self.token}"}
        )

