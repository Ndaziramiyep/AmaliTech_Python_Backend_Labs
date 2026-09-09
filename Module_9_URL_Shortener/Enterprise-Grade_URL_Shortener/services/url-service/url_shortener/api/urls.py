from django.urls import path

from url_shortener.api.views import RedirectUrlView, UrlDetailView, UrlListCreateView

urlpatterns = [
    path("api/v1/urls/", UrlListCreateView.as_view(), name="list-create-url"),
    path("api/v1/urls/<str:short_code>/", UrlDetailView.as_view(), name="url-detail"),
    path("<str:short_code>/", RedirectUrlView.as_view(), name="redirect-url"),
]
