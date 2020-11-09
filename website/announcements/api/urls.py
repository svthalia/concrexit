"""DRF routes defined by the announcements package."""
from rest_framework import routers

from announcements.api import viewsets

router = routers.SimpleRouter()
router.register(r"announcements/slide", viewsets.SlideViewset)
urlpatterns = router.urls
