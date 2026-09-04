from rest_framework import serializers


class ClickEventSerializer(serializers.Serializer):
    """Validates an incoming click-event report before it's handed off to track_click_task."""

    short_code = serializers.CharField(max_length=50)
    owner_id = serializers.IntegerField()
    referrer = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    user_agent = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    ip_address = serializers.IPAddressField(required=False, allow_null=True, default=None)
    city = serializers.CharField(max_length=100, required=False, allow_null=True, default=None)
    country = serializers.CharField(max_length=100, required=False, allow_null=True, default=None)


class UrlClickStatsSerializer(serializers.Serializer):
    """Shapes click-count/last-clicked stats for a single short code."""

    short_code = serializers.CharField()
    click_count = serializers.IntegerField()
    last_clicked_at = serializers.DateTimeField(allow_null=True)


class UserClickSummaryItemSerializer(serializers.Serializer):
    """Shapes one short code's click count within a user's summary list."""

    short_code = serializers.CharField()
    click_count = serializers.IntegerField()


class TimeSeriesPointSerializer(serializers.Serializer):
    """Shapes one day's click count within a time-series breakdown."""

    date = serializers.DateField()
    count = serializers.IntegerField()


class GeoBreakdownItemSerializer(serializers.Serializer):
    """Shapes the click count for one city/country combination."""

    city = serializers.CharField(allow_null=True)
    country = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()


class DetailedAnalyticsSerializer(serializers.Serializer):
    """Shapes the full Premium-only analytics payload: totals, a daily time series, and a geo breakdown."""

    short_code = serializers.CharField()
    click_count = serializers.IntegerField()
    time_series = TimeSeriesPointSerializer(many=True)
    geo_breakdown = GeoBreakdownItemSerializer(many=True)
