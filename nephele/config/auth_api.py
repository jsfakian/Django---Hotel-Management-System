from uuid import uuid4

from django.contrib.auth.models import Group, User
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.models import Guest
from accounts.permissions import get_user_role


class AuthBurstThrottle(AnonRateThrottle):
    rate = '20/minute'


class NepheleTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = get_user_role(user) or 'guest'
        token['username'] = user.username
        token['email'] = user.email
        return token


class NepheleTokenObtainPairView(TokenObtainPairView):
    serializer_class = NepheleTokenObtainPairSerializer
    throttle_classes = [AuthBurstThrottle]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    # Client-supplied roles are ignored; public signup is always guest.
    role = serializers.CharField(max_length=50, required=False, default='guest')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthBurstThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            username = data['email'].split('@')[0]
            if User.objects.filter(username=username).exists():
                username = f"{username}-{uuid4().hex[:8]}"

            user = User.objects.create_user(
                username=username,
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_active=True,
            )

            guest_group, _ = Group.objects.get_or_create(name='guest')
            user.groups.add(guest_group)

            Guest.objects.get_or_create(
                user=user,
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                },
            )

        return Response(
            {
                'user_id': user.id,
                'email': user.email,
                'role': 'guest',
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token') or request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Invalid or already blacklisted refresh token'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthBurstThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {'message': 'Password reset email sent'},
            status=status.HTTP_200_OK,
        )
