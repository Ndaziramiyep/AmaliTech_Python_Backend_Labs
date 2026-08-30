from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from url_shortener.api.auth_views import LoginView, RegisterView
from url_shortener.api.views import (
    RedirectUrlView,
    UrlAnalyticsView,
    UrlDetailView,
    UrlListCreateView,
)

api_v1_urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("urls/", UrlListCreateView.as_view(), name="url-list-create"),
    path("urls/<str:short_code>/", UrlDetailView.as_view(), name="url-detail"),
    path("analytics/<str:short_code>/", UrlAnalyticsView.as_view(), name="url-analytics"),
]

urlpatterns = [
    path("<str:short_code>/", RedirectUrlView.as_view(), name="redirect-url"),
]
