from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async
from datetime import datetime
import pytz
import random
import string
import aiohttp
from .models import ReferralCode, Referral
from apps.authentication.models import User

class EmailHunterService:
    @staticmethod
    async def verify_email(email):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.hunter.io/v2/email-verifier?email={email}&api_key=VOTRE_CLE_API") as response:
                return await response.json()

class ReferralCodeService:
    @staticmethod
    async def generate_unique_code(length=8):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            exists = await ReferralCode.objects.filter(code=code).aexists()
            if not exists:
                return code

    @staticmethod
    async def create_referral_code(user, expires_at):
        await ReferralCode.objects.filter(user=user, is_active=True).aupdate(is_active=False)
        code = await self.generate_unique_code()
        referral_code = await ReferralCode.objects.acreate(
            user=user, 
            code=code, 
            expires_at=expires_at
        )
        cache_key = f'referral_code_{user.email}'
        await cache.aset(cache_key, code, timeout=86400)
        return referral_code

    @staticmethod
    async def get_referral_code_by_email(email):
        cache_key = f'referral_code_{email}'
        cached_code = await cache.aget(cache_key)
        if cached_code:
            return cached_code
        try:
            user = await User.objects.aget(email=email)
            referral_code = await ReferralCode.objects.filter(
                user=user, 
                is_active=True, 
                expires_at__gt=datetime.now(pytz.UTC)
            ).afirst()
            if referral_code:
                await cache.aset(cache_key, referral_code.code, timeout=86400)
                return referral_code.code
        except User.DoesNotExist:
            return None

    @staticmethod
    async def verify_referral_code(code):
        try:
            return await ReferralCode.objects.aget(
                code=code,
                is_active=True,
                expires_at__gt=datetime.now(pytz.UTC)
            )
        except ReferralCode.DoesNotExist:
            return None

class ReferralRegistrationService:
    @staticmethod
    async def register_user_with_referral(email, password, referral_code=None):
        try:
            # Validate referral code if provided
            if referral_code:
                referrer_code = await ReferralCodeService.verify_referral_code(referral_code)
                if not referrer_code:
                    return None, "Invalid referral code"
                
                if referrer_code.user.email == email:
                    return None, "Self-referral is not allowed"

            # Create user
            user = await User.objects.acreate_user(
                email=email,
                password=password
            )

            # Create referral relationship if valid code
            if referral_code and referrer_code:
                await Referral.objects.acreate(
                    referrer=referrer_code.user,
                    referred=user,
                    referral_code=referrer_code
                )
                # Update referral stats
                await referrer_code.user.arefresh_from_db()
                referrer_code.user.total_referrals += 1
                await referrer_code.user.asave()

            return user, None

        except Exception as e:
            return None, str(e)