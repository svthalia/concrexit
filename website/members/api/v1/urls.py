"""DRF routes defined by the members package."""
from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"members", viewsets.MemberViewset)
urlpatterns = router.urls
