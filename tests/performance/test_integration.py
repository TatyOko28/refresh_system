import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.authentication.models import User
from apps.referrals.models import ReferralCode, Referral
from datetime import datetime, timedelta
import pytz

@pytest.mark.django_db
class TestCompleteReferralFlow:
    def test_complete_referral_flow(self, client):
        # 1. Register referrer
        referrer_data = {
            "email": "referrer@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe"
        }
        response = client.post(reverse('user-register'), referrer_data)
        assert response.status_code == status.HTTP_201_CREATED
        referrer_token = response.json()['tokens']['access']

        
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        code_data = {"expires_at": expires_at.isoformat()}
        response = client.post(
            reverse('referral-code-create'),
            code_data,
            HTTP_AUTHORIZATION=f'Bearer {referrer_token}'
        )
        assert response.status_code == status.HTTP_201_CREATED
        referral_code = response.json()['code']

        referred_data = {
            "email": "referred@example.com",
            "password": "testpass123",
            "referral_code": referral_code
        }
        response = client.post(reverse('referral-register'), referred_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        response = client.get(
            reverse('referral-list'),
            HTTP_AUTHORIZATION=f'Bearer {referrer_token}'
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        assert response.json()[0]['referred_email'] == "referred@example.com"

