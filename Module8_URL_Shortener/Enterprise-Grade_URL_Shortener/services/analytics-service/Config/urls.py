from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from analytics.health import health_check

urlpatterns = [
    path("admin/", admin.site.urls),

    path("health/", health_check, name="health"),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path("", include("analytics.api.urls")),
]
