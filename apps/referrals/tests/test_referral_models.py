# File: apps/referrals/tests/test_models.py
import pytest
from django.utils import timezone
from datetime import timedelta
from apps.authentication.models import User
from apps.referrals.models import ReferralCode, Referral

@pytest.mark.django_db
class TestReferralModels:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_create_referral_code(self, user):
        expires_at = timezone.now() + timedelta(days=30)
        referral_code = ReferralCode.objects.create(
            user=user,
            code='TEST123',
            expires_at=expires_at
        )
        assert referral_code.code == 'TEST123'
        assert referral_code.is_active
        assert referral_code.user == user

    def test_create_referral(self, user):
        referrer = user
        referred = User.objects.create_user(
            email='referred@example.com',
            password='testpass123'
        )
        expires_at = timezone.now() + timedelta(days=30)
        referral_code = ReferralCode.objects.create(
            user=referrer,
            code='TEST123',
            expires_at=expires_at
        )
        referral = Referral.objects.create(
            referrer=referrer,
            referred=referred,
            referral_code=referral_code
        )
        assert referral.referrer == referrer
        assert referral.referred == referred
        assert referral.referral_code == referral_code