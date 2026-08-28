"""Router registration for the authenticated URL management API, mounted under /api/v1/."""

from rest_framework.routers import DefaultRouter

from .views import URLViewSet

router = DefaultRouter()
router.register("urls", URLViewSet, basename="url")

urlpatterns = router.urls
