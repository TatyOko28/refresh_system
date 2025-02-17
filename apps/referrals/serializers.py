from rest_framework import serializers
from django.utils import timezone
from .models import ReferralCode, Referral
from apps.authentication.models import User


class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = ['id', 'code', 'is_active', 'expires_at', 'created_at']
        read_only_fields = ['id', 'code', 'created_at']

    def validate(self, data):
        user = self.context['request'].user
        
        # Check if user already has an active referral code
        if self.context['request'].method == 'POST':
            active_code = ReferralCode.objects.filter(
                user=user,
                is_active=True,
                expires_at__gt=timezone.now()
            ).first()
            
            if active_code:
                raise serializers.ValidationError({
                    "non_field_errors": ["You already have an active referral code"]
                })
        
        # Validate expiration date
        if 'expires_at' in data:
            if data['expires_at'] <= timezone.now():
                raise serializers.ValidationError({
                    "expires_at": ["Expiration date must be in the future"]
                })
        
        return data


class ReferralSerializer(serializers.ModelSerializer):
    referrer_email = serializers.EmailField(source='referrer.email', read_only=True)
    referred_email = serializers.EmailField(source='referred.email', read_only=True)

    class Meta:
        model = Referral
        fields = ['id', 'referrer_email', 'referred_email', 'created_at']
        read_only_fields = ['id', 'referrer_email', 'referred_email', 'created_at']


class ReferralRegistrationSerializer(serializers.Serializer):
    referral_code = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value