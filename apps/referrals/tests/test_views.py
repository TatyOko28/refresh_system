# File: apps/referrals/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta
import pytz
from apps.authentication.models import User
from apps.referrals.models import ReferralCode

@pytest.mark.django_db
class TestReferralViews:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_referral_code(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-create')
        
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        data = {
            'expires_at': expires_at.isoformat()
        }
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_active']
        
        # Try to create another active code
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_delete_referral_code(self, api_client, user):
        api_client.force_authenticate(user=user)
        
        # Create a code first
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        referral_code = ReferralCode.objects.create(
            user=user,
            code='TEST123',
            expires_at=expires_at
        )
        
        url = reverse('referral-code-delete', kwargs={'code': 'TEST123'})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify code is inactive
        referral_code.refresh_from_db()
        assert not referral_code.is_active
    
    def test_get_referral_code_by_email(self, api_client, user):
        api_client.force_authenticate(user=user)
        
        # Create a code first
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        referral_code = ReferralCode.objects.create(
            user=user,
            code='TEST123',
            expires_at=expires_at
        )
        
        url = reverse('referral-code-by-email', 
                     kwargs={'email': 'test@example.com'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'TEST123'