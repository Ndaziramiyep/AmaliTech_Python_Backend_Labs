"""Serializers for aggregated analytics data."""

from rest_framework import serializers


class CountryClicksSerializer(serializers.Serializer):
    """Serializes a single country's aggregated click total."""

    country = serializers.CharField(allow_null=True)
    total = serializers.IntegerField()


class DailyClicksSerializer(serializers.Serializer):
    """Serializes a single day's aggregated click total."""

    day = serializers.DateField()
    total = serializers.IntegerField()
