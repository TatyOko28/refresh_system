import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.authentication.models import User


@pytest.mark.django_db
class TestAuthenticationViews:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_user_registration(self, api_client):
        url = reverse('user-register')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user_id' in response.data
        assert 'tokens' in response.data
        assert User.objects.filter(email='test@example.com').exists()
    
    def test_user_login(self, api_client):        
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True  le
        )
        
        url = reverse('user-login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post(url, data)

       
        print(response.data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['tokens']  
        assert 'refresh' in response.data['tokens']

    def test_invalid_login(self, api_client):
        url = reverse('user-login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
