"""Views for creating, managing, and resolving shortened URLs."""

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import ClickTrackingService

from .models import URL
from .permissions import IsOwner
from .serializers import URLCreateSerializer, URLSerializer
from .services import URLShortenerService


class URLViewSet(viewsets.ModelViewSet):
    """Provides CRUD operations for the authenticated user's own shortened URLs."""

    serializer_class = URLSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    lookup_field = "short_code"
    http_method_names = ["get", "post", "put", "delete"]

    def get_queryset(self):
        """Return only the requesting user's URLs, preloaded to avoid N+1 queries."""
        return URL.objects.with_related().filter(owner=self.request.user)

    def get_serializer_class(self):
        """Use the creation serializer for writes and the full serializer otherwise."""
        return URLCreateSerializer if self.action == "create" else URLSerializer

    def create(self, request, *args, **kwargs):
        """Validate the input, delegate creation to the service layer, then return the full representation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        tags = data.pop("tags", [])

        url = URLShortenerService().create_short_url(owner=request.user, **data)
        if tags:
            url.tags.set(tags)

        return Response(URLSerializer(url).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Deactivate the URL instead of deleting it outright, preserving its analytics history."""
        url = self.get_object()
        url.is_active = False
        url.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RedirectURLView(APIView):
    """Publicly resolves a short code or custom alias to its original URL and records a click."""

    permission_classes = [AllowAny]

    def get(self, request, short_code):
        """Look up the target URL, record the click, and issue an HTTP redirect."""
        url = get_object_or_404(
            URL.objects.active_urls(), Q(short_code=short_code) | Q(custom_alias=short_code)
        )
        ClickTrackingService.record(url, request)
        return redirect(url.original_url)
