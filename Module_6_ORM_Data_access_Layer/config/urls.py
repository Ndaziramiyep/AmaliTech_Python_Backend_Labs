"""Root URL configuration wiring together admin, docs, the versioned API, and the public redirect."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.links.views import RedirectURLView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.links.api_urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("<str:short_code>/", RedirectURLView.as_view(), name="redirect-url"),
]
