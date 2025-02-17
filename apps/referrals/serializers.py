# File: apps/referrals/serializers.py
from rest_framework import serializers
from .models import ReferralCode, Referral
from apps.authentication.models import User
from datetime import datetime
import pytz

class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = ['id', 'code', 'is_active', 'expires_at', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        user = self.context['request'].user
        
        # Check if user already has an active referral code
        if self.context['request'].method == 'POST':
            active_code = ReferralCode.objects.filter(
                user=user,
                is_active=True
            ).first()
            
            if active_code:
                raise serializers.ValidationError(
                    "You already have an active referral code"
                )
        
        # Validate expiration date
        if 'expires_at' in data:
            now = datetime.now(pytz.UTC)
            if data['expires_at'] <= now:
                raise serializers.ValidationError(
                    "Expiration date must be in the future"
                )
        
        return data

class ReferralSerializer(serializers.ModelSerializer):
    referrer_email = serializers.EmailField(source='referrer.email', read_only=True)
    referred_email = serializers.EmailField(source='referred.email', read_only=True)

    class Meta:
        model = Referral
        fields = ['id', 'referrer_email', 'referred_email', 'created_at']
        read_only_fields = ['id', 'created_at']

class ReferralRegistrationSerializer(serializers.Serializer):
    referral_code = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
