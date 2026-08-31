from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from url_shortener.models import Url


class UrlCreateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2000)

    def validate_original_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value


class ResolveUrlSerializer(serializers.Serializer):
    short_url = serializers.CharField()
    original_url = serializers.URLField()


class UrlSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()
    owner = serializers.ReadOnlyField(source='owner_email')

    class Meta:
        model = Url
        fields = ['id', 'original_url', 'short_url', 'short_link', 'owner', 'created_at']
        read_only_fields = ['id', 'short_url', 'owner', 'created_at']

    @extend_schema_field(serializers.URLField())
    def get_short_link(self, obj):
        base_url = settings.BASE_URL.rstrip('/')
        return f'{base_url}/{obj.short_url}/'
