from django.db.models import Count, Max
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.api.permissions import IsInternalService
from analytics.api.serializers import (
    ClickEventSerializer,
    UrlClickStatsSerializer,
    UserClickSummaryItemSerializer,
)
from analytics.models import ClickEvent

OWNER_ID_PARAMETER = OpenApiParameter(
    name="owner_id",
    type=int,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Only include clicks recorded under this owner id.",
)


class OwnerIdQuerySerializer(serializers.Serializer):
    owner_id = serializers.IntegerField()


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
    @extend_schema(
        parameters=[OWNER_ID_PARAMETER],
        responses={200: UrlClickStatsSerializer},
        description=(
            "Click count and most recent click timestamp for a short code, "
            "scoped to the given owner_id. Returns zero/null if that owner "
            "has no recorded clicks on this code yet."
        ),
    )
    def get(self, request, short_code):
        query = OwnerIdQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)
        owner_id = query.validated_data['owner_id']

        events = ClickEvent.objects.filter(short_code=short_code, owner_id=owner_id)
        aggregate = events.aggregate(click_count=Count("id"), last_clicked_at=Max("clicked_at"))
        data = {
            "short_code": short_code,
            "click_count": aggregate["click_count"] or 0,
            "last_clicked_at": aggregate["last_clicked_at"],
        }
        return Response(UrlClickStatsSerializer(data).data)


class UserClickSummaryView(APIView):
    @extend_schema(
        parameters=[OWNER_ID_PARAMETER],
        responses={200: UserClickSummaryItemSerializer(many=True)},
        description="Total click counts for every short code owned by owner_id that has at least one recorded click, most-clicked first.",
    )
    def get(self, request):
        query = OwnerIdQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)
        owner_id = query.validated_data['owner_id']

        rows = (
            ClickEvent.objects.filter(owner_id=owner_id)
            .values("short_code")
            .annotate(click_count=Count("id"))
            .order_by("-click_count")
        )
        return Response(UserClickSummaryItemSerializer(rows, many=True).data)
