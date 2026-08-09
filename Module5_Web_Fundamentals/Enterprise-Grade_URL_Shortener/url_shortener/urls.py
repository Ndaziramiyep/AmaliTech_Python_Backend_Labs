from django.urls import path
from .views import CreateShortUrlView, RedirectUrlView

urlpatterns = [
    path("shorten/", CreateShortUrlView.as_view(), name="create-short-url"),
    path("<str:short_code>/", RedirectUrlView.as_view(), name="redirect-url"),
]

