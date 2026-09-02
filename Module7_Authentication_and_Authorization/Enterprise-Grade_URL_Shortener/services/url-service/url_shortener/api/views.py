import json
import random
import string
import threading

from django.conf import settings
from django.core.cache import cache
from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from url_shortener.api.pagination import UrlPagination
from url_shortener.api.permissions import IsOwnerOrReadOnly
from url_shortener.api.serializers import UrlCreateSerializer, UrlSerializer
from url_shortener.api.throttling import TieredUserRateThrottle
from url_shortener.clients import analytics_client
from url_shortener.models import Tag, Url

SHORT_CODE_LENGTH = 6
SHORT_CODE_ALPHABET = string.ascii_letters + string.digits
CACHE_KEY_PREFIX = "url"
FREE_TIER_ACTIVE_URL_LIMIT = 10

# Swagger UI auto-generates its own "current instant" example for any
# date-time field left without an explicit example, which is stale (already
# in the past) by the time you click Execute. Supplying this example
# ourselves — with expires_at left out — stops Swagger from doing that, so
# "Try it out" defaults to a link that never expires instead of one that's
# dead on arrival.
URL_REQUEST_EXAMPLE = OpenApiExample(
    "No expiry (most common)",
    value={
        "original_url": "https://example.com/some/long/path",
        "title": "My link",
        "tags": ["news"],
    },
    request_only=True,
)


def _cache_key(short_code):
    """Builds the cache key used to store a short code's URL data."""
    return f"{CACHE_KEY_PREFIX}:{short_code}"


def _lookup_url(code):
    """Finds a Url by its short_url or its custom_alias — either identifier resolves the same row."""
    return Url.objects.filter(Q(short_url=code) | Q(custom_alias=code)).first()


def _identifiers_for(url_obj):
    """Returns every code (short_url, and custom_alias if set) that resolves to this Url."""
    codes = [url_obj.short_url]
    if url_obj.custom_alias:
        codes.append(url_obj.custom_alias)
    return codes


def _cache_url(url_obj):
    """Caches a Url instance's data under every identifier that resolves to it."""
    data = {
        "original_url": url_obj.original_url,
        "owner_id": url_obj.owner_id,
        "owner_email": url_obj.owner_email,
        "is_active": url_obj.is_active,
        "expires_at": url_obj.expires_at.isoformat() if url_obj.expires_at else None,
    }
    encoded = json.dumps(data)
    for code in _identifiers_for(url_obj):
        cache.set(_cache_key(code), encoded, timeout=settings.URL_CACHE_TIMEOUT_SECONDS)
    return data


def _invalidate_cache(url_obj):
    """Removes every identifier that resolves to this Url from the cache."""
    for code in _identifiers_for(url_obj):
        cache.delete(_cache_key(code))


def _get_or_create_tags(names):
    """Fetches or creates a Tag for each given name, returning the matching Tag instances."""
    return [Tag.objects.get_or_create(name=name)[0] for name in names]


def _generate_unique_short_code():
    """Generates a random short code that isn't already in use as a short_url or custom_alias."""
    while True:
        code = "".join(random.choice(SHORT_CODE_ALPHABET) for _ in range(SHORT_CODE_LENGTH))
        if _lookup_url(code) is None:
            return code


def _resolve_short_code(short_code):
    """Looks up a short code's URL data (cache first, then the database), or None if inactive/expired/missing."""
    cached = cache.get(_cache_key(short_code))
    if cached:
        data = json.loads(cached)
    else:
        url_obj = _lookup_url(short_code)
        if url_obj is None:
            return None
        data = _cache_url(url_obj)

    if not data["is_active"]:
        return None
    if data["expires_at"] and timezone.now() >= parse_datetime(data["expires_at"]):
        return None
    return data


def _is_available(url_obj):
    """True if this Url instance is active and not past its expiry, i.e. safe to serve/display."""
    if not url_obj.is_active:
        return False
    if url_obj.expires_at and timezone.now() >= url_obj.expires_at:
        return False
    return True


class UrlListCreateView(APIView):
    """Lists the caller's own URLs (all URLs for admins), with pagination and tag search, and creates new ones."""

    permission_classes = [IsAuthenticated]
    pagination_class = UrlPagination

    def get_throttles(self):
        """Applies the tiered rate limit to creation only — listing isn't throttled."""
        if self.request.method == 'POST':
            return [TieredUserRateThrottle()]
        return []

    @extend_schema(
        parameters=[],
        responses={200: UrlSerializer(many=True)},
        description=(
            "List your own shortened URLs, paginated (?page=, ?page_size=) and "
            "filterable by tag (?tag=news). Staff/admin users see every URL "
            "across all owners instead of just their own."
        ),
    )
    def get(self, request):
        """Lists all URLs for admins, or only the caller's own URLs otherwise; supports ?tag= filtering."""
        urls = Url.objects.all() if request.user.is_staff else Url.objects.filter(owner_id=request.user.id)
        tag = request.query_params.get('tag')
        if tag:
            urls = urls.filter(tags__name=tag)
        urls = urls.prefetch_related('tags').distinct().order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(urls, request, view=self)
        return paginator.get_paginated_response(UrlSerializer(page, many=True).data)

    @extend_schema(
        request=UrlCreateSerializer,
        examples=[URL_REQUEST_EXAMPLE],
        responses={201: UrlSerializer, 403: None, 429: None},
        description=(
            "Create a new shortened URL. Requires authentication "
            "(register or log in via auth-service first, then send the access "
            "token via the Authorize button as 'Bearer <your-access-token>'). "
            "A custom_alias requires Premium/Admin tier. Free tier is capped at "
            "10 active URLs. Rate limited per tier (Free: 100/day, Premium/Admin: 1000/day). "
            "Omit expires_at (or send it as null) for a link that never expires — "
            "don't use whatever value Swagger's 'Try it out' pre-fills there, it's "
            "just a schema placeholder and is stale by the time you submit."
        ),
    )
    def post(self, request):
        """Validates the submitted URL, enforces the Free-tier active-URL cap, generates a short code, and persists it."""
        if not request.user.is_staff and request.user.tier != 'Premium':
            active_count = Url.objects.filter(owner_id=request.user.id, is_active=True).count()
            if active_count >= FREE_TIER_ACTIVE_URL_LIMIT:
                return Response(
                    {"detail": f"Free tier is limited to {FREE_TIER_ACTIVE_URL_LIMIT} active URLs. Upgrade to Premium for unlimited URLs."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = UrlCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        short_code = _generate_unique_short_code()
        url_obj = Url.objects.create(
            original_url=data['original_url'],
            short_url=short_code,
            owner_id=request.user.id,
            owner_email=request.user.email,
            custom_alias=data.get('custom_alias'),
            title=data.get('title'),
            description=data.get('description'),
            favicon=data.get('favicon'),
            is_active=data.get('is_active', True),
            expires_at=data.get('expires_at'),
        )
        if data.get('tags'):
            url_obj.tags.set(_get_or_create_tags(data['tags']))
        _cache_url(url_obj)

        return Response(UrlSerializer(url_obj).data, status=status.HTTP_201_CREATED)


class UrlDetailView(APIView):
    """Publicly retrieves a short code's full details, and lets its owner or an admin update or delete it."""

    permission_classes = [IsOwnerOrReadOnly]

    def get_throttles(self):
        """Applies the tiered rate limit to updates and deletes only — the public GET isn't throttled."""
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [TieredUserRateThrottle()]
        return []

    def _get_object(self, short_code):
        """Fetches the Url by short_code or custom_alias (404 if missing), enforcing owner/admin for write requests."""
        url_obj = _lookup_url(short_code)
        if url_obj is None:
            raise Http404
        self.check_object_permissions(self.request, url_obj)
        return url_obj

    def _update(self, request, short_code, partial):
        """Shared PUT/PATCH implementation: validates and applies whichever fields were submitted."""
        url_obj = self._get_object(short_code)
        serializer = UrlCreateSerializer(
            data=request.data, partial=partial, context={'request': request, 'instance': url_obj},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = dict(serializer.validated_data)
        tag_names = data.pop('tags', None)
        for field, value in data.items():
            setattr(url_obj, field, value)
        url_obj.save()
        if tag_names is not None:
            url_obj.tags.set(_get_or_create_tags(tag_names))

        _invalidate_cache(url_obj)
        _cache_url(url_obj)

        return Response(UrlSerializer(url_obj).data)

    @extend_schema(
        responses={200: UrlSerializer, 404: None},
        description=(
            "Retrieve a short code (or custom alias)'s full details — anyone "
            "may read this, same as the public redirect. Returns 404 if the "
            "code is unknown, inactive, or past its expires_at."
        ),
    )
    def get(self, request, short_code):
        """Returns the full Url representation if it exists, is active, and isn't expired."""
        url_obj = _lookup_url(short_code)
        if url_obj is None or not _is_available(url_obj):
            raise Http404
        return Response(UrlSerializer(url_obj).data)

    @extend_schema(
        request=UrlCreateSerializer,
        examples=[URL_REQUEST_EXAMPLE],
        responses={200: UrlSerializer, 400: None, 403: None, 404: None, 429: None},
        description=(
            "Fully update a short code's fields. Only that URL's owner or a "
            "staff/admin user may do this; anyone else gets a 403. A "
            "custom_alias requires Premium/Admin tier."
        ),
    )
    def put(self, request, short_code):
        """Fully updates a short code's fields for the caller who owns it or administers it."""
        return self._update(request, short_code, partial=False)

    @extend_schema(
        request=UrlCreateSerializer,
        examples=[URL_REQUEST_EXAMPLE],
        responses={200: UrlSerializer, 403: None, 404: None, 429: None},
        description=(
            "Partially update a short code's fields (original_url, custom_alias, "
            "title, description, favicon, is_active, expires_at, tags). Only "
            "that URL's owner or a staff/admin user may do this; anyone else "
            "gets a 403. A custom_alias requires Premium/Admin tier."
        ),
    )
    def patch(self, request, short_code):
        """Updates whichever fields were submitted, for a short code the caller owns or administers."""
        return self._update(request, short_code, partial=True)

    @extend_schema(
        responses={204: None, 403: None, 404: None, 429: None},
        description=(
            "Delete a short code, cascading to its click history in "
            "analytics-service. Only that URL's owner or a staff/admin user "
            "may do this; anyone else gets a 403."
        ),
    )
    def delete(self, request, short_code):
        """Deletes a short code the caller owns or administers, clearing its cache and cascading to analytics-service."""
        url_obj = self._get_object(short_code)
        _invalidate_cache(url_obj)
        codes = _identifiers_for(url_obj)
        url_obj.delete()
        threading.Thread(target=analytics_client.delete_click_events, args=(codes,), daemon=True).start()

        return Response(status=status.HTTP_204_NO_CONTENT)


class RedirectUrlView(APIView):
    """Redirects a short code to its original URL, counts the click, and reports it to analytics-service."""

    @extend_schema(
        responses={302: None, 404: None},
        description=(
            "Redirect to the original URL. Returns 404 if the code is unknown, "
            "inactive, or past its expires_at. "
            "Open the short link directly in your browser to test it — "
            "Swagger's \"Try it out\" reports a fetch failure for "
            "cross-origin redirect targets because the browser's fetch() "
            "call follows the redirect and is then blocked by CORS on the "
            "destination site, even though this endpoint responds "
            "correctly with a 302."
        ),
    )
    def get(self, request, short_code):
        """Resolves the short code, counts the click, and redirects — reporting to analytics-service happens in the background, never delaying the redirect."""
        result = _resolve_short_code(short_code)
        if result is None:
            raise Http404

        Url.objects.filter(Q(short_url=short_code) | Q(custom_alias=short_code)).update(
            click_count=F('click_count') + 1
        )
        threading.Thread(
            target=analytics_client.record_click,
            kwargs=dict(
                short_code=short_code,
                owner_id=result['owner_id'],
                referrer=request.META.get('HTTP_REFERER', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=request.META.get('REMOTE_ADDR'),
            ),
            daemon=True,
        ).start()

        return redirect(result['original_url'])
