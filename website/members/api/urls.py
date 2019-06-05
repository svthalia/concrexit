from rest_framework import routers

from members.api import viewsets

router = routers.SimpleRouter()
router.register(r'members', viewsets.MemberViewset)
urlpatterns = router.urls
