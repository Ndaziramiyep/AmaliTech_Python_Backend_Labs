"""Serializers for the accounts app."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validates registration input and creates a new user with a securely hashed password."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        """Create the user through Django's helper so the password is hashed, not stored raw."""
        return User.objects.create_user(**validated_data)
