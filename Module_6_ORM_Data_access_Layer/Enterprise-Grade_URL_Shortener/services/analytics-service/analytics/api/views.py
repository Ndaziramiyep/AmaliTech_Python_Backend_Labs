from django.db.models import Count, Max
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.api.permissions import IsInternalService
from analytics.api.serializers import (
    ClickEventSerializer,
    UrlClickStatsSerializer,
    UserClickSummaryItemSerializer,
)
from analytics.models import ClickEvent


class RecordClickView(APIView):
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
        serializer = ClickEventSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)


class UrlClickStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UrlClickStatsSerializer},
        description=(
            "Click count and most recent click timestamp for a short code "
            "you own. Returns zero/null if that code has no recorded clicks yet."
        ),
    )
    def get(self, request, short_code):
        events = ClickEvent.objects.filter(short_code=short_code, owner_id=request.user.id)
        aggregate = events.aggregate(click_count=Count("id"), last_clicked_at=Max("clicked_at"))
        data = {
            "short_code": short_code,
            "click_count": aggregate["click_count"] or 0,
            "last_clicked_at": aggregate["last_clicked_at"],
        }
        return Response(UrlClickStatsSerializer(data).data)


class UserClickSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserClickSummaryItemSerializer(many=True)},
        description="Total click counts for every short code you own that has at least one recorded click, most-clicked first.",
    )
    def get(self, request):
        rows = (
            ClickEvent.objects.filter(owner_id=request.user.id)
            .values("short_code")
            .annotate(click_count=Count("id"))
            .order_by("-click_count")
        )
        return Response(UserClickSummaryItemSerializer(rows, many=True).data)
