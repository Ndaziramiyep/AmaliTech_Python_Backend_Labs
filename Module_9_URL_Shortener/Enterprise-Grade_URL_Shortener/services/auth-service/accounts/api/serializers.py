from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import User


class RegisterSerializer(serializers.Serializer):
    """Validates and creates a new user from an email, password, and password confirmation."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        """Rejects an email that already belongs to an existing user."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value

    def validate(self, attrs):
        """Rejects the payload if password and confirm_password don't match."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        """Creates a new Django User from the validated email and password."""
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
        )


class LoginSerializer(serializers.Serializer):
    """Validates email/password credentials and authenticates the user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticates the user by email and password, raising an error if invalid."""
        user = User.objects.filter(email__iexact=attrs['email']).first()
        if user is not None:
            user = authenticate(username=user.username, password=attrs['password'])
        if user is None:
            raise serializers.ValidationError("Invalid email or password")
        attrs['user'] = user
        return attrs
