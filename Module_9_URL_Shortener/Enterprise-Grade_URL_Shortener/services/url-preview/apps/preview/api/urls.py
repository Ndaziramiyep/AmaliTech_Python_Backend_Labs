from django.urls import path

from apps.preview.api.views import PreviewView

urlpatterns = [
    path("internal/preview/", PreviewView.as_view(), name="url-preview-fetch"),
]
