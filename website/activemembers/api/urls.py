"""DRF routes defined by the activemembers package"""
from rest_framework import routers

from activemembers.api import viewsets

router = routers.SimpleRouter()
router.register(r"activemembers/groups", viewsets.MemberGroupViewset)
urlpatterns = router.urls
