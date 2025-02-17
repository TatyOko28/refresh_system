# File: apps/authentication/views.py
from apps.integrations.emailhunter_service import EmailHunterService
from apps.integrations.clearbit_service import ClearbitService
from asgiref.sync import sync_to_async
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer

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
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Successfully logged in",
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
            401: "Unauthorized",
            400: "Bad Request"
        }
    )
    async def post(self, request):
        """
        Authenticate a user and return JWT tokens.
        """
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                email = serializer.validated_data['email']
                password = serializer.validated_data['password']

                # Get user asynchronously
                try:
                    user = await User.objects.aget(email=email)
                except User.DoesNotExist:
                    return Response(
                        {'error': 'No user found with this email'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                # Check password
                if not await sync_to_async(user.check_password)(password):
                    return Response(
                        {'error': 'Invalid credentials'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                # Get user's clearbit data if exists
                clearbit_data = None
                if user.clearbit_data:
                    clearbit_data = user.clearbit_data
                else:
                    # Try to enrich user data if not already present
                    clearbit_data = await ClearbitService.enrich_user_data(email)
                    if clearbit_data:
                        user.clearbit_data = clearbit_data
                        await sync_to_async(user.save)()

                return Response({
                    'user_id': str(user.id),
                    'email': user.email,
                    'clearbit_data': clearbit_data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)