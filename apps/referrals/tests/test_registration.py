# File: apps/referrals/tests/test_registration.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta
import pytz
from apps.authentication.models import User
from apps.referrals.models import ReferralCode, Referral
from apps.referrals.exceptions import InvalidReferralCodeException, SelfReferralException

@pytest.mark.django_db
class TestReferralRegistration:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def referrer(self):
        return User.objects.create_user(
            email='referrer@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def active_referral_code(self, referrer):
        return ReferralCode.objects.create(
            user=referrer,
            code='TEST123',
            expires_at=datetime.now(pytz.UTC) + timedelta(days=7)
        )

    def test_successful_registration(self, api_client, active_referral_code):
        url = reverse('referral-register')
        data = {
            'referral_code': active_referral_code.code,
            'email': 'referred@example.com',
            'password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        
        # Verify referral relationship
        referral = Referral.objects.first()
        assert referral.referrer == active_referral_code.user
        assert referral.referred.email == 'referred@example.com'

    def test_invalid_referral_code(self, api_client):
        url = reverse('referral-register')
        data = {
            'referral_code': 'INVALID',
            'email': 'referred@example.com',
            'password': 'testpass123'
        }

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_self_referral(self, api_client, active_referral_code, referrer):
        url = reverse('referral-register')
        data = {
            'referral_code': active_referral_code.code,
            'email': referrer.email,
            'password': 'testpass123'
        }

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_referral_stats(self, api_client, referrer, active_referral_code):
        # Create some referrals
        for i in range(3):
            referred = User.objects.create_user(
                email=f'referred{i}@example.com',
                password='testpass123'
            )
            Referral.objects.create(
                referrer=referrer,
                referred=referred,
                referral_code=active_referral_code
            )

        api_client.force_authenticate(user=referrer)
        url = reverse('referral-stats')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_referrals'] == 3
        assert len(response.data['recent_referrals']) <= 5
        assert response.data['active_code'] is not None