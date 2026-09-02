from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.api.views import LoginView, RegisterView

urlpatterns = [
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
