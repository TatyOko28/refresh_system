from datetime import datetime
import pytz
import random
import string
from django.core.cache import cache
from django.conf import settings
from .models import ReferralCode, Referral
from django.contrib.auth import get_user_model
from .exceptions import InvalidReferralCodeException, SelfReferralException

User = get_user_model()

class ReferralCodeService:
    CACHE_TIMEOUT = 86400  
    CODE_LENGTH = 8

    @staticmethod
    def generate_unique_code(length=CODE_LENGTH):
        
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not ReferralCode.objects.filter(code=code).exists():
                return code
            attempts += 1
            
        raise Exception("Failed to generate unique code after maximum attempts")

    @staticmethod
    def create_referral_code(user, expires_at):       
        
        from django.db import transaction
        
        with transaction.atomic():           
            ReferralCode.objects.filter(user=user, is_active=True).update(is_active=False)
            
            # Create new code
            code = ReferralCodeService.generate_unique_code()
            referral_code = ReferralCode.objects.create(
                user=user,
                code=code,
                expires_at=expires_at
            )
            
            # Cache the new code
            cache_key = f'referral_code_{user.email}'
            cache.set(cache_key, code, timeout=ReferralCodeService.CACHE_TIMEOUT)
            
            return referral_code

    @staticmethod
    def get_referral_code_by_email(email):
        
        cache_key = f'referral_code_{email}'
        
        # Try cache first
        cached_code = cache.get(cache_key)
        if cached_code:
            # Verify the cached code is still valid
            if ReferralCodeService.verify_referral_code(cached_code):
                return cached_code
            else:
                cache.delete(cache_key)
        
        try:
            user = User.objects.get(email=email)
            referral_code = ReferralCode.objects.filter(
                user=user,
                is_active=True,
                expires_at__gt=datetime.now(pytz.UTC)
            ).first()
            
            if referral_code:
                cache.set(cache_key, referral_code.code, 
                         timeout=ReferralCodeService.CACHE_TIMEOUT)
                return referral_code.code
            
        except User.DoesNotExist:
            pass
        
        return None

    @staticmethod
    def verify_referral_code(code):
        
        try:
            return ReferralCode.objects.get(
                code=code,
                is_active=True,
                expires_at__gt=datetime.now(pytz.UTC)
            )
        except ReferralCode.DoesNotExist:
            return None


class ReferralRegistrationService:
    @staticmethod
    def register_with_referral(referral_code, email, password, **extra_data):
       
        from django.db import transaction
        
        # First verify the referral code
        referral_code_obj = ReferralCodeService.verify_referral_code(referral_code)
        if not referral_code_obj:
            raise InvalidReferralCodeException("Invalid or expired referral code")

        # Check for existing user and self-referral
        try:
            existing_user = User.objects.get(email=email)
            if existing_user:
                if referral_code_obj.user.email == email:
                    raise SelfReferralException("You cannot use your own referral code")
                else:
                    raise SelfReferralException("User with this email already exists")
        except User.DoesNotExist:
            pass

        # Create user and referral record in a transaction
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                **extra_data
            )

            Referral.objects.create(
                referrer=referral_code_obj.user,
                referred=user,
                referral_code=referral_code_obj
            )

            return user

    @staticmethod
    def get_referral_stats(user):
        
        cache_key = f'referral_stats_{user.id}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
            
        referrals = Referral.objects.filter(referrer=user)
        stats = {
            'total_referrals': referrals.count(),
            'recent_referrals': list(referrals.order_by('-created_at')[:5]),
            'active_code': ReferralCode.objects.filter(
                user=user,
                is_active=True,
                expires_at__gt=datetime.now(pytz.UTC)
            ).first()
        }
        
        # Cache for 1 hour since this data changes more frequently
        cache.set(cache_key, stats, timeout=3600)
        
        return stats