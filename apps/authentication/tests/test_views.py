# File: apps/authentication/tests/test_views.py

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
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    @pytest.fixture
    def active_referral_code(self, user):
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        return ReferralCode.objects.create(
            user=user,
            code='TEST123',
            expires_at=expires_at,
            is_active=True
        )

    def test_create_referral_code(self, api_client, user):
        """Test creating a new referral code"""
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-create')
        
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        data = {
            'expires_at': expires_at.isoformat()
        }
        
        # First creation should succeed
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_active'] is True
        assert response.data['user'] == str(user.id)
        assert 'code' in response.data
        
        # Second creation should deactivate the first code
        response2 = api_client.post(url, data)
        assert response2.status_code == status.HTTP_201_CREATED
        
        # Verify first code is now inactive
        first_code = ReferralCode.objects.get(code=response.data['code'])
        assert first_code.is_active is False

    def test_create_referral_code_validation(self, api_client, user):
        """Test referral code creation with invalid data"""
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-create')
        
        # Test with expired date
        expired_date = datetime.now(pytz.UTC) - timedelta(days=1)
        data = {
            'expires_at': expired_date.isoformat()
        }
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'expires_at' in response.data
    
    def test_delete_referral_code(self, api_client, user, active_referral_code):
        """Test deleting a referral code"""
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-delete', kwargs={'code': active_referral_code.code})
        
        # Delete should succeed
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify code is inactive
        active_referral_code.refresh_from_db()
        assert active_referral_code.is_active is False
        
        # Second delete should fail
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_referral_code(self, api_client, user):
        """Test deleting a nonexistent referral code"""
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-delete', kwargs={'code': 'NONEXISTENT'})
        
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_referral_code_by_email(self, api_client, user, active_referral_code):
        """Test retrieving a referral code by email"""
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-by-email', kwargs={'email': user.email})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == active_referral_code.code

    def test_get_referral_code_by_email_nonexistent(self, api_client, user):
        """Test retrieving a referral code for nonexistent email"""
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-by-email', kwargs={'email': 'nonexistent@example.com'})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'No active referral code found'

    def test_get_referral_code_by_email_inactive(self, api_client, user, active_referral_code):
        """Test retrieving an inactive referral code"""
        # Deactivate the code
        active_referral_code.is_active = False
        active_referral_code.save()
        
        api_client.force_authenticate(user=user)
        url = reverse('referral-code-by-email', kwargs={'email': user.email})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'No active referral code found'

    def test_unauthorized_access(self, api_client):
        """Test accessing endpoints without authentication"""
        # Test create
        create_url = reverse('referral-code-create')
        response = api_client.post(create_url, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test delete
        delete_url = reverse('referral-code-delete', kwargs={'code': 'TEST123'})
        response = api_client.delete(delete_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test get by email
        get_url = reverse('referral-code-by-email', kwargs={'email': 'test@example.com'})
        response = api_client.get(get_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED