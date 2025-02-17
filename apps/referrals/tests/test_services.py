import pytest
import pytest_asyncio
from django.utils import timezone
from asgiref.sync import sync_to_async
from apps.authentication.models import User
from apps.referrals.services import ReferralCodeService

@pytest.mark.django_db
class TestReferralCodeService:
    @pytest_asyncio.fixture
    async def user(self):
        @sync_to_async
        def create_user():
            return User.objects.create_user(
                email="test@example.com", 
                password="password"
            )
        return await create_user()

    @pytest.mark.asyncio
    async def test_create_referral_code(self, user):
        expires_at = timezone.now() + timezone.timedelta(days=7)
        referral_code = await ReferralCodeService.create_referral_code(user, expires_at)
        assert referral_code.user.id == user.id
        assert referral_code.is_active is True

    @pytest.mark.asyncio
    async def test_get_referral_code_by_email(self, user):
        expires_at = timezone.now() + timezone.timedelta(days=7)
        referral_code = await ReferralCodeService.create_referral_code(user, expires_at)
        code = await ReferralCodeService.get_referral_code_by_email(user.email)
        assert code == referral_code.code

    @pytest.mark.asyncio
    async def test_verify_referral_code(self, user):
        expires_at = timezone.now() + timezone.timedelta(days=7)
        referral_code = await ReferralCodeService.create_referral_code(user, expires_at)
        verified_code = await ReferralCodeService.verify_referral_code(referral_code.code)
        assert verified_code.id == referral_code.id