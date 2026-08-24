"""Views exposing click analytics for a URL owner's own links."""

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.links.models import URL

from .models import Click
from .permissions import IsPremiumUser
from .serializers import CountryClicksSerializer, DailyClicksSerializer


class URLAnalyticsView(APIView):
    """Exposes time-series and geographic click analytics for a single owned URL."""

    permission_classes = [IsAuthenticated, IsPremiumUser]

    def get(self, request, short_code):
        """Return click totals grouped by country and by day for the requested URL."""
        url = get_object_or_404(URL, short_code=short_code, owner=request.user)
        clicks = Click.objects.filter(url=url)

        by_country = clicks.values("country").annotate(total=Count("id")).order_by("-total")
        by_day = (
            clicks.annotate(day=TruncDate("clicked_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )

        return Response(
            {
                "short_code": url.short_code,
                "total_clicks": clicks.count(),
                "by_country": CountryClicksSerializer(by_country, many=True).data,
                "by_day": DailyClicksSerializer(by_day, many=True).data,
            }
        )
