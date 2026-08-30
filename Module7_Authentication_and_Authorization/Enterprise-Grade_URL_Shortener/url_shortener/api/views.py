from django.db.models import Count, F
from django.db.models.functions import TruncDate
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from url_shortener.api.serializers import UrlCreateSerializer, UrlSerializer, UrlUpdateSerializer
from url_shortener.models import Click, Tag, Url
from url_shortener.permissions import IsOwnerOrReadOnly, IsPremiumUser
from url_shortener.services.url_shortener_service import UrlShortenerService


def _get_tags(names):
    return [Tag.objects.get_or_create(name=name)[0] for name in names]


class UrlListCreateView(APIView):
    service_class = UrlShortenerService
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        return Url.objects.with_related().filter(owner=request.user).order_by('-created_at')

    @extend_schema(responses={200: UrlSerializer(many=True)}, description="List the authenticated user's URLs.")
    def get(self, request):
        urls = self.get_queryset(request)
        return Response(UrlSerializer(urls, many=True).data)

    @extend_schema(
        request=UrlCreateSerializer,
        responses={201: UrlSerializer},
        description="Create a new shortened URL owned by the authenticated user.",
    )
    def post(self, request):
        serializer = UrlCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = dict(serializer.validated_data)

        if not request.user.has_premium_access():
            if data.get('custom_alias'):
                return Response(
                    {'custom_alias': 'Custom aliases are available to premium accounts only.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            active_count = Url.objects.active_urls().filter(owner=request.user).count()
            if active_count >= request.user.FREE_TIER_ACTIVE_URL_LIMIT:
                return Response(
                    {
                        'detail': (
                            f'Free tier is limited to {request.user.FREE_TIER_ACTIVE_URL_LIMIT} active URLs. '
                            'Upgrade to premium for unlimited URLs.'
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        tag_names = data.pop('tags', [])

        url_obj = self.service_class().create_short_url(
            data.pop('original_url'), request.user, tags=_get_tags(tag_names), **data
        )

        return Response(UrlSerializer(url_obj).data, status=status.HTTP_201_CREATED)


class UrlDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, short_code):
        obj = get_object_or_404(Url.objects.with_related(), short_code=short_code)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(responses={200: UrlSerializer}, description="Retrieve details for one of the authenticated user's URLs.")
    def get(self, request, short_code):
        return Response(UrlSerializer(self.get_object(short_code)).data)

    @extend_schema(
        request=UrlUpdateSerializer,
        responses={200: UrlSerializer},
        description="Update a URL owned by the authenticated user.",
    )
    def put(self, request, short_code):
        url_obj = self.get_object(short_code)
        serializer = UrlUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = dict(serializer.validated_data)
        tag_names = data.pop('tags', None)
        for field, value in data.items():
            setattr(url_obj, field, value)
        url_obj.save()
        if tag_names is not None:
            url_obj.tags.set(_get_tags(tag_names))

        return Response(UrlSerializer(url_obj).data)

    @extend_schema(
        responses={204: None},
        description="Deactivate a URL owned by the authenticated user (soft delete).",
    )
    def delete(self, request, short_code):
        url_obj = self.get_object(short_code)
        url_obj.is_active = False
        url_obj.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RedirectUrlView(APIView):
    @extend_schema(
        responses={302: None, 404: None},
        description=(
            "Redirect to the original URL and record a click. "
            "Open the short link directly in your browser to test it — "
            "Swagger's \"Try it out\" reports a fetch failure for "
            "cross-origin redirect targets because the browser's fetch() "
            "call follows the redirect and is then blocked by CORS on the "
            "destination site, even though this endpoint responds "
            "correctly with a 302."
        ),
    )
    def get(self, request, short_code):
        url_obj = Url.objects.active_urls().filter(short_code=short_code).first()
        if url_obj is None:
            raise Http404

        Url.objects.filter(pk=url_obj.pk).update(click_count=F('click_count') + 1)
        Click.objects.create(
            url=url_obj,
            ip_address=self._client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referrer=request.META.get('HTTP_REFERER') or None,
        )

        return redirect(url_obj.original_url)

    @staticmethod
    def _client_ip(request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class UrlAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsPremiumUser]

    @extend_schema(
        responses={200: None},
        description="Time-series and geographic click analytics for one of the authenticated user's URLs. Premium accounts only.",
    )
    def get(self, request, short_code):
        url_obj = get_object_or_404(Url, short_code=short_code)
        if url_obj.owner_id != request.user.id:
            raise Http404

        clicks = Click.objects.filter(url=url_obj)

        clicks_by_country = list(
            clicks.exclude(country__isnull=True)
            .values('country')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        clicks_by_day = list(
            clicks.annotate(day=TruncDate('clicked_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        top_referrers = list(
            clicks.exclude(referrer__isnull=True)
            .values('referrer')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        return Response({
            'short_code': url_obj.short_code,
            'total_clicks': url_obj.click_count,
            'clicks_by_country': clicks_by_country,
            'clicks_by_day': clicks_by_day,
            'top_referrers': top_referrers,
        })
