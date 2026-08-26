from django.urls import path

from url_shortener.api.views import CreateShortUrlView, RedirectUrlView

urlpatterns = [
    path("api/urls/", CreateShortUrlView.as_view(), name="create-short-url"),
    path("<str:short_code>/", RedirectUrlView.as_view(), name="redirect-url"),
]
