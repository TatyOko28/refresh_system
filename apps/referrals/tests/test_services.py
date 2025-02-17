# File: apps/referrals/tests/test_services.py
import pytest
from datetime import datetime, timedelta
import pytz
from django.core.cache import cache
from apps.authentication.models import User
from apps.referrals.models import ReferralCode
from apps.referrals.services import ReferralCodeService

@pytest.mark.django_db
class TestReferralCodeService:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_generate_unique_code(self):
        code = ReferralCodeService.generate_unique_code()
        assert len(code) == 8
        assert code.isalnum()
    
    def test_create_referral_code(self, user):
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        referral_code = ReferralCodeService.create_referral_code(user, expires_at)
        
        assert referral_code.user == user
        assert referral_code.is_active
        assert referral_code.expires_at == expires_at
        
        # Test cache
        cache_key = f'referral_code_{user.email}'
        cached_code = cache.get(cache_key)
        assert cached_code == referral_code.code
    
    def test_get_referral_code_by_email(self, user):
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        referral_code = ReferralCodeService.create_referral_code(user, expires_at)
        
        code = ReferralCodeService.get_referral_code_by_email(user.email)
        assert code == referral_code.code
    
    def test_verify_referral_code(self, user):
        expires_at = datetime.now(pytz.UTC) + timedelta(days=7)
        referral_code = ReferralCodeService.create_referral_code(user, expires_at)
        
        verified_code = ReferralCodeService.verify_referral_code(referral_code.code)
        assert verified_code == referral_code

