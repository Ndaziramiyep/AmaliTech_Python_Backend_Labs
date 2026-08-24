"""Serializers for the links app."""

from django.conf import settings
from rest_framework import serializers

from apps.tags.models import Tag

from .models import URL


class URLCreateSerializer(serializers.ModelSerializer):
    """Validates the input needed to create a new shortened URL."""

    tags = serializers.SlugRelatedField(
        slug_field="name", queryset=Tag.objects.all(), many=True, required=False
    )

    class Meta:
        model = URL
        fields = ["original_url", "custom_alias", "tags", "title", "description", "expires_at"]

    def validate_custom_alias(self, value):
        """Reject a custom alias that another URL has already claimed."""
        if value and URL.objects.filter(custom_alias=value).exists():
            raise serializers.ValidationError("This alias is already taken.")
        return value


class URLSerializer(serializers.ModelSerializer):
    """Represents a shortened URL for read and update responses, including its public link."""

    tags = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    short_link = serializers.SerializerMethodField()
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = URL
        fields = [
            "id",
            "owner",
            "original_url",
            "short_code",
            "custom_alias",
            "short_link",
            "tags",
            "title",
            "description",
            "favicon",
            "is_active",
            "expires_at",
            "click_count",
            "created_at",
        ]
        read_only_fields = ["id", "owner", "short_code", "click_count", "created_at"]

    def get_short_link(self, obj) -> str:
        """Build the full public redirect link for this shortened URL."""
        base_url = settings.BASE_URL.rstrip("/")
        code = obj.custom_alias or obj.short_code
        return f"{base_url}/{code}/"
