from django.db.models import Count, Max
from django.db.models.functions import TruncDate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.api.permissions import IsInternalService, IsPremiumOrAdmin
from analytics.api.serializers import (
    ClickEventSerializer,
    DetailedAnalyticsSerializer,
    UrlClickStatsSerializer,
    UserClickSummaryItemSerializer,
)
from analytics.models import ClickEvent


class RecordClickView(APIView):
    """Internal endpoint used by url-service to report a short-link click, or cascade-delete a deleted URL's click history."""

    permission_classes = [IsInternalService]

    @extend_schema(
        request=ClickEventSerializer,
        responses={201: None},
        description=(
            "Internal endpoint used by url-service to report that a short "
            "link was visited. Requires the X-Internal-Key header shared "
            "between the two services — not intended for public/browser use."
        ),
    )
    def post(self, request):
        """Validate and record a reported click event."""
        serializer = ClickEventSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={204: None},
        description=(
            "Internal endpoint used by url-service to cascade-delete click "
            "history when a URL is deleted. Body: {\"short_codes\": [...]}"
            " — deletes every ClickEvent matching any of the given codes."
        ),
    )
    def delete(self, request):
        """Deletes every ClickEvent matching any of the given short_codes."""
        short_codes = request.data.get('short_codes') or []
        if not short_codes:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ClickEvent.objects.filter(short_code__in=short_codes).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UrlClickStatsView(APIView):
    """Returns click-count and last-clicked stats for a short code the caller owns."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UrlClickStatsSerializer},
        description=(
            "Click count and most recent click timestamp for a short code "
            "you own. Returns zero/null if that code has no recorded clicks yet."
        ),
    )
    def get(self, request, short_code):
        """Aggregate click count and last-clicked timestamp for the given short code."""
        events = ClickEvent.objects.filter(short_code=short_code, owner_id=request.user.id)
        aggregate = events.aggregate(click_count=Count("id"), last_clicked_at=Max("clicked_at"))
        data = {
            "short_code": short_code,
            "click_count": aggregate["click_count"] or 0,
            "last_clicked_at": aggregate["last_clicked_at"],
        }
        return Response(UrlClickStatsSerializer(data).data)


class UserClickSummaryView(APIView):
    """Returns per-short-code click totals for every code the caller owns, most-clicked first."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserClickSummaryItemSerializer(many=True)},
        description="Total click counts for every short code you own that has at least one recorded click, most-clicked first.",
    )
    def get(self, request):
        """Aggregate click counts grouped by short code for the requesting user."""
        rows = (
            ClickEvent.objects.filter(owner_id=request.user.id)
            .values("short_code")
            .annotate(click_count=Count("id"))
            .order_by("-click_count")
        )
        return Response(UserClickSummaryItemSerializer(rows, many=True).data)


class DetailedAnalyticsView(APIView):
    """Premium/Admin-only time-series and geo-location analytics for a short code."""

    permission_classes = [IsAuthenticated, IsPremiumOrAdmin]

    @extend_schema(
        responses={200: DetailedAnalyticsSerializer, 403: None},
        description=(
            "Daily time-series click counts and a city/country geo breakdown "
            "for a short code you own (any owner's, for staff/admin). "
            "Requires Premium or Admin tier — Free tier gets a 403. city/country "
            "are null for clicks whose IP couldn't be geolocated."
        ),
    )
    def get(self, request, short_code):
        """Aggregates this short code's click events into a daily time series and a city/country breakdown."""
        owner_filter = {} if request.user.is_staff else {"owner_id": request.user.id}
        events = ClickEvent.objects.filter(short_code=short_code, **owner_filter)

        time_series = (
            events.annotate(date=TruncDate("clicked_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        geo_breakdown = (
            events.values("city", "country")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        data = {
            "short_code": short_code,
            "click_count": events.count(),
            "time_series": list(time_series),
            "geo_breakdown": list(geo_breakdown),
        }
        return Response(DetailedAnalyticsSerializer(data).data)
