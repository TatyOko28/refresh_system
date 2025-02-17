# apps/referrals/views.py

import json
from django.http import JsonResponse
from django.views import View
from rest_framework import status
from asgiref.sync import sync_to_async

# IMPORTS NÉCESSAIRES
from django.core.cache import cache
from apps.referrals.models import ReferralCode, Referral
from apps.referrals.serializers import (
    ReferralCodeSerializer,
    ReferralRegistrationSerializer,
    ReferralSerializer
)
from apps.referrals.services import ReferralCodeService, ReferralRegistrationService
from apps.integrations.services import EmailHunterService  # Ajustez le chemin selon votre projet
from rest_framework_simplejwt.tokens import RefreshToken


class ReferralCodeCreateView(View):
    async def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Utilisation d'une fonction asynchrone pour instancier le serializer
        serializer = await sync_to_async(ReferralCodeSerializer)(
            data=data, 
            context={'request': request}
        )
        is_valid = await sync_to_async(serializer.is_valid)()
        if is_valid:
            expires_at = serializer.validated_data['expires_at']
            referral_code = await ReferralCodeService.create_referral_code(
                user=request.user, 
                expires_at=expires_at
            )
            # On récupère les données sérialisées via une lambda pour éviter des problèmes de synchronisation
            serialized_data = await sync_to_async(lambda: ReferralCodeSerializer(referral_code).data)()
            return JsonResponse(serialized_data, status=status.HTTP_201_CREATED)
        
        errors = await sync_to_async(lambda: serializer.errors)()
        return JsonResponse(errors, status=status.HTTP_400_BAD_REQUEST)


class ReferralCodeView(View):
    async def delete(self, request, code):
        try:
            referral_code = await ReferralCode.objects.aget(
                code=code, 
                user=request.user
            )
            referral_code.is_active = False
            await referral_code.asave()
            await cache.adelete(f'referral_code_{request.user.email}')
            return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
        except ReferralCode.DoesNotExist:
            return JsonResponse(
                {"error": "Referral code not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    async def get(self, request, email=None):
        if email:
            code = await ReferralCodeService.get_referral_code_by_email(email)
            if code:
                return JsonResponse({"code": code})
            return JsonResponse(
                {"error": "No active referral code found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        referrals = await sync_to_async(list)(Referral.objects.filter(referrer=request.user))
        serialized_data = await sync_to_async(lambda: ReferralSerializer(referrals, many=True).data)()
        return JsonResponse(serialized_data, safe=False)


class ReferralRegistrationView(View):
    async def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = await sync_to_async(ReferralRegistrationSerializer)(data=data)
        is_valid = await sync_to_async(serializer.is_valid)()
        if is_valid:
            try:
                referral_code = await ReferralCodeService.verify_referral_code(
                    serializer.validated_data['referral_code']
                )
                if not referral_code:
                    return JsonResponse(
                        {'error': 'Invalid or expired referral code'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                email_verification = await EmailHunterService.verify_email(
                    serializer.validated_data['email']
                )
                if not email_verification.get('is_valid'):
                    return JsonResponse(
                        {'error': 'Invalid email address'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if referral_code.user.email == serializer.validated_data['email']:
                    return JsonResponse(
                        {'error': 'Cannot use your own referral code'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                referred_user = await ReferralRegistrationService.create_user(
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    first_name=serializer.validated_data.get('first_name', ''),
                    last_name=serializer.validated_data.get('last_name', '')
                )

                await Referral.objects.acreate(
                    referrer=referral_code.user, 
                    referred=referred_user, 
                    referral_code=referral_code
                )

                refresh = await sync_to_async(RefreshToken.for_user)(referred_user)
                return JsonResponse({
                    'user_id': str(referred_user.id),
                    'email': referred_user.email,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token)
                    }
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        errors = await sync_to_async(lambda: serializer.errors)()
        return JsonResponse(errors, status=status.HTTP_400_BAD_REQUEST)


class ReferralStatsView(View):
    async def get(self, request):
        stats = await ReferralRegistrationService.get_referral_stats(request.user)
        recent_referrals = await sync_to_async(lambda: ReferralSerializer(stats['recent_referrals'], many=True).data)()
        active_code = None
        if stats['active_code']:
            active_code = await sync_to_async(lambda: ReferralCodeSerializer(stats['active_code']).data)()
        return JsonResponse({
            'total_referrals': stats['total_referrals'],
            'recent_referrals': recent_referrals,
            'active_code': active_code
        })
