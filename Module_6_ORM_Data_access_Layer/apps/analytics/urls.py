"""URL routes for the analytics app."""

from django.urls import path

from .views import URLAnalyticsView

urlpatterns = [
    path("<str:short_code>/", URLAnalyticsView.as_view(), name="url-analytics"),
]
