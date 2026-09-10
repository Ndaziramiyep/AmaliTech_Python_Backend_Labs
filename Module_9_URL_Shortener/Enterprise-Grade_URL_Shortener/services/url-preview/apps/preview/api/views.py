import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.preview.api.permissions import IsInternalService
from apps.preview.api.serializers import PreviewRequestSerializer, PreviewResponseSerializer
from apps.preview.api.services.errors import CircuitOpenError, InvalidURLError, PreviewFetchError
from apps.preview.api.services.preview_service import PreviewService
from apps.preview.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Documents the header IsInternalService actually checks, so Swagger UI's
# "Try it out" renders an input field for it instead of leaving callers to
# guess from the description text alone (and get a bare 401 back).
INTERNAL_TOKEN_HEADER = OpenApiParameter(
    name="X-Internal-Token",
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description="Shared secret proving this call came from shortener, not the public internet.",
)


class PreviewView(APIView):
    """Internal-only endpoint: fetches a destination page's title/description/favicon, called by shortener right after a short URL is created."""

    permission_classes = [IsInternalService]

    @extend_schema(
        request=PreviewRequestSerializer,
        parameters=[INTERNAL_TOKEN_HEADER],
        responses={200: PreviewResponseSerializer, 400: None, 502: None},
        description=(
            "Fetches the destination page at `url` and returns its title, "
            "meta-description, and favicon. Rejects a URL whose hostname "
            "resolves to a private/loopback/reserved/multicast address "
            "(400, SSRF guard). Retries a transient failure with backoff, "
            "and short-circuits (502) with no network call at all while the "
            "destination domain's circuit breaker is open."
        ),
    )
    def post(self, request):
        """Validates the destination URL and returns its title/description/favicon, or an error status if it couldn't be fetched."""
        serializer = PreviewRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = PreviewService(get_redis_client())
        try:
            result = service.fetch(serializer.validated_data['url'])
        except InvalidURLError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (CircuitOpenError, PreviewFetchError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result, status=status.HTTP_200_OK)
