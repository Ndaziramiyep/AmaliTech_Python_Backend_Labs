from django.conf import settings
from django.db.models import Q
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from url_shortener.models import Url


def _is_premium_or_admin(user):
    """True if the given caller may use Premium-only features like a custom alias."""
    return bool(getattr(user, "is_staff", False) or getattr(user, "tier", "Free") in ("Premium", "Admin"))


class UrlCreateSerializer(serializers.Serializer):
    """Validates the payload for creating a new short URL, or partially updating an existing one."""

    original_url = serializers.URLField(max_length=2000)
    custom_alias = serializers.CharField(max_length=50, required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True)
    favicon = serializers.CharField(max_length=2000, required=False, allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)

    def validate_original_url(self, value):
        """Rejects URLs without an http:// or https:// scheme."""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def validate_custom_alias(self, value):
        """Rejects a custom_alias below Premium tier, and one already used by another URL."""
        if value is None:
            return value

        request = self.context.get('request')
        if request is not None and not _is_premium_or_admin(request.user):
            raise serializers.ValidationError("Custom aliases are a Premium/Admin feature.")

        existing = Url.objects.filter(Q(short_url=value) | Q(custom_alias=value))
        instance = self.context.get('instance')
        if instance is not None:
            existing = existing.exclude(pk=instance.pk)
        if existing.exists():
            raise serializers.ValidationError("This alias is already taken.")
        return value


class UrlSerializer(serializers.ModelSerializer):
    """Serializes a Url model instance for API responses."""

    short_link = serializers.SerializerMethodField()
    owner = serializers.ReadOnlyField(source='owner_email')
    tags = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta:
        """Configures which Url fields this serializer exposes and which are read-only."""

        model = Url
        fields = [
            'id', 'original_url', 'short_url', 'short_link', 'custom_alias', 'owner',
            'is_active', 'expires_at', 'title', 'description', 'favicon', 'click_count',
            'tags', 'created_at',
        ]
        read_only_fields = ['id', 'short_url', 'owner', 'click_count', 'created_at']

    @extend_schema_field(serializers.URLField())
    def get_short_link(self, obj):
        """Builds the fully-qualified short link URL for the given Url instance."""
        base_url = settings.BASE_URL.rstrip('/')
        return f'{base_url}/{obj.short_url}/'
