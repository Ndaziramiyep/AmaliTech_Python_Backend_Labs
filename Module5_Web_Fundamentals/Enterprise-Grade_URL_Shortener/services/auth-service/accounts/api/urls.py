from django.urls import path

from accounts.api.views import LoginView, RegisterView

urlpatterns = [
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
]
