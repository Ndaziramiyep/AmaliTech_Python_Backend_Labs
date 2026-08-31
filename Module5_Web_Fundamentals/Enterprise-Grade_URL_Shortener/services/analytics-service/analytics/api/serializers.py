from rest_framework import serializers

from analytics.models import ClickEvent


class ClickEventSerializer(serializers.Serializer):
    short_code = serializers.CharField(max_length=10)
    owner_id = serializers.IntegerField()
    referrer = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    user_agent = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    ip_address = serializers.IPAddressField(required=False, allow_null=True, default=None)

    def create(self, validated_data):
        return ClickEvent.objects.create(**validated_data)


class UrlClickStatsSerializer(serializers.Serializer):
    short_code = serializers.CharField()
    click_count = serializers.IntegerField()
    last_clicked_at = serializers.DateTimeField(allow_null=True)


class UserClickSummaryItemSerializer(serializers.Serializer):
    short_code = serializers.CharField()
    click_count = serializers.IntegerField()
