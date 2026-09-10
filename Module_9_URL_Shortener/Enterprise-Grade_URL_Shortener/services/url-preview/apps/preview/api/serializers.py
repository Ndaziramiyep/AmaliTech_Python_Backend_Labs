from rest_framework import serializers


class PreviewRequestSerializer(serializers.Serializer):
    """Validates the destination URL submitted for a preview."""

    url = serializers.URLField(max_length=2000)


class PreviewResponseSerializer(serializers.Serializer):
    """Documents the shape of a successful preview response."""

    title = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    favicon = serializers.CharField(allow_null=True)
