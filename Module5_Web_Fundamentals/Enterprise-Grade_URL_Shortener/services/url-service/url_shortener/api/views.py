from django.http import Http404
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from url_shortener.api.serializers import ResolveUrlSerializer, UrlCreateSerializer, UrlSerializer
from url_shortener.clients import analytics_client
from url_shortener.services.url_shortener_service import UrlShortenerService


class CreateShortUrlView(APIView):
    service_class = UrlShortenerService

    @extend_schema(
        request=UrlCreateSerializer,
        responses={201: UrlSerializer},
        description="Create a new shortened URL for the given owner_id/owner_email.",
    )
    def post(self, request):
        serializer = UrlCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url_obj = self.service_class().create_short_url(
            serializer.validated_data['original_url'],
            serializer.validated_data['owner_id'],
            serializer.validated_data['owner_email'],
        )

        return Response(UrlSerializer(url_obj).data, status=status.HTTP_201_CREATED)


class ResolveShortUrlView(APIView):
    service_class = UrlShortenerService

    @extend_schema(
        responses={200: ResolveUrlSerializer, 404: None},
        description=(
            "Look up a short code and return the original URL as JSON, "
            "without redirecting. Use this to read the original URL "
            "(e.g. from Swagger) instead of the plain redirect endpoint below, "
            "which sends back a 302 rather than a readable body."
        ),
    )
    def get(self, request, short_code):
        result = self.service_class().resolve(short_code)
        if result is None:
            raise Http404
        return Response({'short_url': short_code, 'original_url': result['original_url']})


class RedirectUrlView(APIView):
    service_class = UrlShortenerService

    @extend_schema(
        responses={302: None, 404: None},
        description=(
            "Redirect to the original URL. "
            "Open the short link directly in your browser to test it — "
            "Swagger's \"Try it out\" reports a fetch failure for "
            "cross-origin redirect targets because the browser's fetch() "
            "call follows the redirect and is then blocked by CORS on the "
            "destination site, even though this endpoint responds "
            "correctly with a 302."
        ),
    )
    def get(self, request, short_code):
        result = self.service_class().resolve(short_code)
        if result is None:
            raise Http404

        analytics_client.record_click(
            short_code=short_code,
            owner_id=result['owner_id'],
            referrer=request.META.get('HTTP_REFERER', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return redirect(result['original_url'])
