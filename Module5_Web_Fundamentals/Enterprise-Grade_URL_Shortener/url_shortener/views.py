from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from drf_spectacular.utils import extend_schema

from .serializer import UrlSerializer, UrlCreateSerializer
from .services import UrlShortenerService
from .models import Url


class CreateShortUrlView(APIView):
    @extend_schema(
        request=UrlCreateSerializer,
        responses={201: UrlSerializer},
        description="Create a new shortened URL"
    )
    def post(self, request):
        serializer = UrlCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        url_obj = UrlShortenerService.create_short_url(
            serializer.validated_data['original_url']
        )
        
        cache.set(f'url:{url_obj.short_url}', url_obj.original_url, timeout=3600)
        
        return Response(UrlSerializer(url_obj).data, status=status.HTTP_201_CREATED)


class RedirectUrlView(APIView):
    @extend_schema(
        responses={302: None, 404: None},
        description="Redirect to the original URL"
    )
    def get(self, request, short_code):
        original_url = cache.get(f'url:{short_code}')

        if not original_url:
            url_obj = get_object_or_404(Url, short_url=short_code)
            original_url = url_obj.original_url
            cache.set(f'url:{short_code}', original_url, timeout=3600)
        
        return redirect(original_url)