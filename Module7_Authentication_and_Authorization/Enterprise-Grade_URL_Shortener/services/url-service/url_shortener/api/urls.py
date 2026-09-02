from django.urls import path

from url_shortener.api.views import RedirectUrlView, UrlDetailView, UrlListCreateView

urlpatterns = [
    path("api/v1/urls/", UrlListCreateView.as_view(), name="list-create-url"),
    path("api/v1/urls/<str:short_code>/", UrlDetailView.as_view(), name="url-detail"),
    # Deliberately unversioned and outside /api/ — this is the public-facing
    # short link itself (e.g. http://host/abc123/), not an API call.
    path("<str:short_code>/", RedirectUrlView.as_view(), name="redirect-url"),
]
