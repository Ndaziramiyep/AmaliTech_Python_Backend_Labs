from django.urls import path

from preview.views import PreviewView

urlpatterns = [
    path("api/v1/preview/", PreviewView.as_view(), name="url-preview"),
]
