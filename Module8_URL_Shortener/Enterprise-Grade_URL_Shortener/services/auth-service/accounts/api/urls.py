from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.api.views import InternalTokenValidateView, LoginView, RegisterView

urlpatterns = [
    path("api/v1/auth/register/", RegisterView.as_view(), name="register"),
    path("api/v1/auth/login/", LoginView.as_view(), name="login"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path(
        "api/v1/auth/internal/token/validate/",
        InternalTokenValidateView.as_view(),
        name="internal-token-validate",
    ),
]
