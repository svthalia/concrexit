"""DRF routes defined by the announcements package."""
from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"announcements/slides", viewsets.SlideViewset)
urlpatterns = router.urls
