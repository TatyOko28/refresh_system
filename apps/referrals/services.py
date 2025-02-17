# File: apps/referrals/services.py
from datetime import datetime
import pytz
import random
import string
from django.core.cache import cache
from .models import ReferralCode, Referral
from apps.authentication.models import User

class ReferralCodeService:
    @staticmethod
    def generate_unique_code(length=8):
        """Generate a unique referral code"""
        while True:
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=length))
            if not ReferralCode.objects.filter(code=code).exists():
                return code

    @staticmethod
    def create_referral_code(user, expires_at):
        """Create a new referral code for user"""
        # Deactivate any existing active codes
        ReferralCode.objects.filter(user=user, is_active=True).update(
            is_active=False)
        
        # Create new code
        code = ReferralCodeService.generate_unique_code()
        referral_code = ReferralCode.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
        
        # Cache the new code
        cache_key = f'referral_code_{user.email}'
        cache.set(cache_key, code, timeout=86400)  # 24 hours
        
        return referral_code

    @staticmethod
    def get_referral_code_by_email(email):
        """Get active referral code by user email"""
        # Try to get from cache first
        cache_key = f'referral_code_{email}'
        cached_code = cache.get(cache_key)
        
        if cached_code:
            return cached_code
        
        try:
            user = User.objects.get(email=email)
            referral_code = ReferralCode.objects.filter(
                user=user,
                is_active=True,
                expires_at__gt=datetime.now(pytz.UTC)
            ).first()
            
            if referral_code:
                # Update cache
                cache.set(cache_key, referral_code.code, timeout=86400)
                return referral_code.code
            
        except User.DoesNotExist:
            pass
        
        return None

    @staticmethod
    def verify_referral_code(code):
        """Verify if a referral code is valid"""
        try:
            referral_code = ReferralCode.objects.get(
                code=code,
                is_active=True,
                expires_at__gt=datetime.now(pytz.UTC)
            )
            return referral_code
        except ReferralCode.DoesNotExist:
            return None

class ReferralRegistrationService:
    @staticmethod
    def register_with_referral(referral_code, email, password, **extra_data):
        """Register a new user with a referral code"""
        # Verify the referral code
        referral_code_obj = ReferralCodeService.verify_referral_code(referral_code)
        if not referral_code_obj:
            raise InvalidReferralCodeException()

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists")

        # Prevent self-referral
        if referral_code_obj.user.email == email:
            raise SelfReferralException()

        # Create the new user
        referred_user = User.objects.create_user(
            email=email,
            password=password,
            **extra_data
        )

        # Create the referral relationship
        Referral.objects.create(
            referrer=referral_code_obj.user,
            referred=referred_user,
            referral_code=referral_code_obj
        )

        return referred_user

    @staticmethod
    def get_referral_stats(user):
        """Get referral statistics for a user"""
        referrals = Referral.objects.filter(referrer=user)
        return {
            'total_referrals': referrals.count(),
            'recent_referrals': referrals.order_by('-created_at')[:5],
            'active_code': ReferralCode.objects.filter(
                user=user,
                is_active=True,
                expires_at__gt=datetime.now(pytz.UTC)
            ).first()
        }

