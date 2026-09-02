from django.urls import path

from analytics.api.views import RecordClickView, UrlClickStatsView, UserClickSummaryView

urlpatterns = [
    path("api/events/click/", RecordClickView.as_view(), name="record-click"),
    path("api/analytics/urls/<str:short_code>/", UrlClickStatsView.as_view(), name="url-click-stats"),
    path("api/analytics/summary/", UserClickSummaryView.as_view(), name="user-click-summary"),
]
