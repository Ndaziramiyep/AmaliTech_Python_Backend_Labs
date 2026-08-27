from django.http import Http404
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from url_shortener.api.serializers import UrlCreateSerializer, UrlSerializer
from url_shortener.services.url_shortener_service import UrlShortenerService


class CreateShortUrlView(APIView):
    service_class = UrlShortenerService
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UrlCreateSerializer,
        responses={201: UrlSerializer},
        description=(
            "Create a new shortened URL. Requires authentication "
            "(register or log in first, then send the token via "
            "the Authorize button as 'Token <your-token>')."
        ),
    )
    def post(self, request):
        serializer = UrlCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url_obj = self.service_class().create_short_url(
            serializer.validated_data['original_url'], request.user
        )

        return Response(UrlSerializer(url_obj).data, status=status.HTTP_201_CREATED)


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
        original_url = self.service_class().resolve(short_code)
        if original_url is None:
            raise Http404
        return redirect(original_url)
