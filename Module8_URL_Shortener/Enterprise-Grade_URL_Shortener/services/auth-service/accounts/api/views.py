from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.api.serializers import LoginSerializer, RegisterSerializer


class LoginRateThrottle(AnonRateThrottle):
    """Limits login attempts per IP to 5/minute, independent of register's throttle."""

    scope = 'login'


class TokenResponseSerializer(serializers.Serializer):
    """Describes the JSON shape returned for a successful registration or login."""

    id = serializers.IntegerField()
    email = serializers.EmailField()
    access = serializers.CharField()
    refresh = serializers.CharField()


def _tokens_for_user(user):
    """Builds a JWT access/refresh token pair embedding the user's email, is_staff, and tier claims."""
    refresh = RefreshToken.for_user(user)
    # Embed email, is_staff, and tier as custom claims so downstream services
    # (url-service, analytics-service) can read them straight off the token
    # instead of calling back here or keeping their own Users table —
    # is_staff/tier are what those services treat as "admin"/plan for
    # role-based access and tiered rate limiting.
    refresh['email'] = user.email
    refresh['is_staff'] = user.is_staff
    refresh['tier'] = user.tier
    access = refresh.access_token
    access['email'] = user.email
    access['is_staff'] = user.is_staff
    access['tier'] = user.tier
    return {
        'id': user.id,
        'email': user.email,
        'access': str(access),
        'refresh': str(refresh),
    }


class RegisterView(APIView):
    """Registers a new user account and returns JWT tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: TokenResponseSerializer},
        description="Register a new user account with email, password, and password confirmation. Returns JWT access and refresh tokens.",
    )
    def post(self, request):
        """Validates registration data, creates the user, and returns JWT tokens."""
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        return Response(_tokens_for_user(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticates a user and returns JWT tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
        description="Log in with email and password to receive JWT access and refresh tokens.",
    )
    def post(self, request):
        """Validates login credentials and returns JWT tokens for the authenticated user."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        return Response(_tokens_for_user(user))
