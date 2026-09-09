from django.urls import path

from analytics.api.views import (
    DetailedAnalyticsView,
    RecordClickView,
    UrlClickStatsView,
    UserClickSummaryView,
)

urlpatterns = [
    path("api/v1/events/click/", RecordClickView.as_view(), name="record-click"),
    path("api/v1/analytics/urls/<str:short_code>/", UrlClickStatsView.as_view(), name="url-click-stats"),
    path("api/v1/analytics/summary/", UserClickSummaryView.as_view(), name="user-click-summary"),
    path("api/v1/analytics/<str:short_code>/", DetailedAnalyticsView.as_view(), name="detailed-analytics"),
]
