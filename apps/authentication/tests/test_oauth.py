import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.authentication.models import User
from rest_framework.exceptions import AuthenticationFailed


@pytest.mark.django_db
class TestGoogleOAuth:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @patch('apps.authentication.oauth2.GoogleOAuth2.validate_google_auth_code')
    @patch('apps.authentication.oauth2.GoogleOAuth2.get_google_user_info')
    def test_google_auth_success(self, mock_get_user_info, mock_validate_code, api_client):
        # Mock return values
        mock_validate_code.return_value = 'mock_access_token'
        mock_get_user_info.return_value = {
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User',
            'email_verified': True
        }

        url = reverse('google-auth')
        data = {
            'code': 'mock_auth_code',
            'redirect_uri': 'http://localhost:8000/callback'
        }

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert 'user_id' in response.data
        
        # Verify user was created
        user = User.objects.get(email='test@example.com')
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.email_verified == True

    @patch('apps.authentication.oauth2.GoogleOAuth2.validate_google_auth_code')
    def test_google_auth_invalid_code(self, mock_validate_code, api_client):
        mock_validate_code.side_effect = AuthenticationFailed('Invalid code')

        url = reverse('google-auth')
        data = {
            'code': 'invalid_code',
            'redirect_uri': 'http://localhost:8000/callback'
        }

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

