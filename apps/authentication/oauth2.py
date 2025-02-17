import requests
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from .models import User

class GoogleOAuth2:
    """Google OAuth2 authentication helper class"""
    GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

    @staticmethod
    def validate_google_auth_code(*, code: str, redirect_uri: str):
        data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }

        response = requests.post(
            GoogleOAuth2.GOOGLE_ACCESS_TOKEN_OBTAIN_URL,
            data=data,
        )

        if not response.ok:
            raise AuthenticationFailed('Failed to obtain access token from Google.')

        access_token = response.json()['access_token']

        return access_token

    @staticmethod
    def get_google_user_info(*, access_token: str):
        response = requests.get(
            GoogleOAuth2.GOOGLE_USER_INFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        if not response.ok:
            raise AuthenticationFailed('Failed to obtain user info from Google.')

        return response.json()






