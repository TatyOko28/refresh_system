# File: apps/authentication/tests/test_models.py
import pytest
from django.core.exceptions import ValidationError
from apps.authentication.models import User

@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin.email == 'admin@example.com'
        assert admin.is_active
        assert admin.is_staff
        assert admin.is_superuser

    def test_user_creation_without_email(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='testpass123')

    def test_email_normalization(self):
        user = User.objects.create_user(
            email='TEST@ExAmPlE.com',
            password='testpass123'
        )
        assert user.email == 'TEST@example.com'

    def test_get_full_name(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        assert user.get_full_name() == 'John Doe'

    def test_get_short_name(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        assert user.get_short_name() == 'John'

