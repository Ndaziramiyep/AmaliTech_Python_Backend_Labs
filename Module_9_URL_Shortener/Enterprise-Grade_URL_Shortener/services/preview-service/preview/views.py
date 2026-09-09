import logging

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from preview.fetcher import PreviewFetchError, fetch_preview
from preview.permissions import IsInternalService

logger = logging.getLogger(__name__)


class PreviewRequestSerializer(serializers.Serializer):
    """Validates the destination URL submitted for a preview."""

    url = serializers.URLField(max_length=2000)


class PreviewResponseSerializer(serializers.Serializer):
    """Documents the shape of a successful preview response."""

    title = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    favicon = serializers.CharField(allow_null=True)


class PreviewView(APIView):
    """Internal-only endpoint: fetches a destination page's title/description/favicon, called by url-service when a short URL is created."""

    permission_classes = [IsInternalService]

    @extend_schema(
        request=PreviewRequestSerializer,
        responses={200: PreviewResponseSerializer, 400: None, 502: None},
        description=(
            "Fetches the destination page at `url` and returns its title, "
            "meta-description, and favicon. Retries a connection failure or "
            "5xx response with backoff; a domain that keeps failing trips a "
            "per-domain circuit breaker and is short-circuited (502) for a "
            "cooldown period instead of being retried on every call."
        ),
    )
    def post(self, request):
        """Validates the destination URL and returns its title/description/favicon, or 502 if it couldn't be fetched."""
        serializer = PreviewRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            preview = fetch_preview(serializer.validated_data['url'])
        except PreviewFetchError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(preview, status=status.HTTP_200_OK)
