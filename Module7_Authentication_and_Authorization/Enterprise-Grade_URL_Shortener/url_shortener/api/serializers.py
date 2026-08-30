from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from url_shortener.models import Tag, Url


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class UrlCreateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2000)
    custom_alias = serializers.CharField(max_length=10, required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_null=True)
    description = serializers.CharField(max_length=500, required=False, allow_null=True)
    favicon = serializers.CharField(max_length=2000, required=False, allow_null=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)

    def validate_original_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def validate_custom_alias(self, value):
        if value and Url.objects.filter(short_code=value).exists():
            raise serializers.ValidationError("This alias is already taken")
        return value


class UrlUpdateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2000, required=False)
    title = serializers.CharField(max_length=255, required=False, allow_null=True)
    description = serializers.CharField(max_length=500, required=False, allow_null=True)
    favicon = serializers.CharField(max_length=2000, required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)


class UrlSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()
    owner = serializers.ReadOnlyField(source='owner.username')
    tags = TagSerializer(many=True, read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Url
        fields = [
            'id', 'original_url', 'short_code', 'custom_alias', 'short_link',
            'owner', 'tags', 'is_active', 'is_expired', 'expires_at',
            'title', 'description', 'favicon', 'click_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'short_code', 'owner', 'click_count', 'created_at', 'updated_at']

    @extend_schema_field(serializers.URLField())
    def get_short_link(self, obj):
        base_url = settings.BASE_URL.rstrip('/')
        return f'{base_url}/{obj.short_code}/'

    @extend_schema_field(serializers.BooleanField())
    def get_is_expired(self, obj):
        return obj.is_expired()
