from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from url_shortener.api.auth_serializers import LoginSerializer, RegisterSerializer


class TokenResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    access = serializers.CharField()
    refresh = serializers.CharField()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'id': user.id,
        'email': user.email,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: TokenResponseSerializer},
        description="Register a new user account with email, password, and password confirmation. Returns JWT access and refresh tokens.",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        return Response(_tokens_for_user(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
        description="Log in with email and password to receive JWT access and refresh tokens.",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        return Response(_tokens_for_user(user))
