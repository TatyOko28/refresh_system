from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from asgiref.sync import sync_to_async
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserRegistrationSerializer, UserLoginSerializer, GoogleAuthSerializer
from apps.integrations.emailhunter_service import EmailHunterService
from apps.integrations.clearbit_service import ClearbitService
from .oauth2 import GoogleOAuth2

User = get_user_model()


class UserRegistrationView(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User successfully registered",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'clearbit_data': openapi.Schema(type=openapi.TYPE_OBJECT),
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
    async def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            email_verification = await EmailHunterService.verify_email(email)
            if email_verification and not email_verification['is_valid']:
                return Response({'error': 'Invalid email address'}, status=status.HTTP_400_BAD_REQUEST)
            user = await sync_to_async(serializer.save)()
            clearbit_data = await ClearbitService.enrich_user_data(email)
            if clearbit_data:
                user.clearbit_data = clearbit_data
                await sync_to_async(user.save)()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user_id': str(user.id),
                'email': user.email,
                'clearbit_data': clearbit_data,
                'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)},
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user_id': str(user.id),
                    'email': user.email,
                    'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)},
                })
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        redirect_uri = serializer.validated_data['redirect_uri']
        try:
            access_token = GoogleOAuth2.validate_google_auth_code(code=code, redirect_uri=redirect_uri)
        except AuthenticationFailed as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_data = GoogleOAuth2.get_google_user_info(access_token=access_token)
        except AuthenticationFailed as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'email_verified': user_data.get('email_verified', False)
            }
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            'user_id': str(user.id),
            'email': user.email,
            'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)},
        })
