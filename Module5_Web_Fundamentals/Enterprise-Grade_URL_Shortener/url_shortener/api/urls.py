from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from url_shortener.api.auth_views import LoginView, RegisterView
from url_shortener.api.views import CreateShortUrlView, RedirectUrlView, ResolveShortUrlView

urlpatterns = [
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/urls/", CreateShortUrlView.as_view(), name="create-short-url"),
    path("api/urls/<str:short_code>/", ResolveShortUrlView.as_view(), name="resolve-short-url"),
    path("<str:short_code>/", RedirectUrlView.as_view(), name="redirect-url"),
]
