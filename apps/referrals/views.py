from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
from .services import ReferralCodeService, ReferralRegistrationService
from .serializers import ReferralCodeSerializer, ReferralSerializer, ReferralRegistrationSerializer
from .models import ReferralCode, Referral
from django.views.generic import CreateView
from django.core.exceptions import ValidationError


class ReferralCodeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ReferralCodeSerializer,
        responses={201: ReferralCodeSerializer, 400: "Bad Request"}
    )
    def post(self, request):
        serializer = ReferralCodeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            referral_code = ReferralCodeService.create_referral_code(
                user=request.user, expires_at=serializer.validated_data['expires_at']
            )
            return Response(ReferralCodeSerializer(referral_code).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReferralCodeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, code):
        try:
            referral_code = ReferralCode.objects.get(code=code, user=request.user)
            referral_code.is_active = False
            referral_code.save()
            cache_key = f'referral_code_{request.user.email}'
            cache.delete(cache_key)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ReferralCode.DoesNotExist:
            return Response({"error": "Referral code not found"}, status=status.HTTP_404_NOT_FOUND)


class ReferralCodeByEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, email):
        code = ReferralCodeService.get_referral_code_by_email(email)
        if code:
            return Response({"code": code})
        return Response({"error": "No active referral code found"}, status=status.HTTP_404_NOT_FOUND)


class ReferralListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        referrals = Referral.objects.filter(referrer=request.user)
        serializer = ReferralSerializer(referrals, many=True)
        return Response(serializer.data)


class ReferralRegistrationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=ReferralRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Successfully registered with referral",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        serializer = ReferralRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = ReferralRegistrationService.register_with_referral(
                    referral_code=serializer.validated_data['referral_code'],
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    first_name=serializer.validated_data.get('first_name', ''),
                    last_name=serializer.validated_data.get('last_name', '')
                )
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user_id': str(user.id),
                    'email': user.email,
                    'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)},
                }, status=status.HTTP_201_CREATED)
            except (InvalidReferralCodeException, SelfReferralException) as e:
                return Response({'error': str(e)}, status=e.status_code)
            except serializers.ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReferralStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = ReferralRegistrationService.get_referral_stats(request.user)
        return Response({
            'total_referrals': stats['total_referrals'],
            'recent_referrals': ReferralSerializer(stats['recent_referrals'], many=True).data,
            'active_code': ReferralCodeSerializer(stats['active_code']).data if stats['active_code'] else None
        })
