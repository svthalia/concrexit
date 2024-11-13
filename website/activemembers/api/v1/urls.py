from rest_framework import routers

from activemembers.api.v1 import viewsets

router = routers.SimpleRouter()
router.register(r"activemembers/groups", viewsets.MemberGroupViewset)
urlpatterns = router.urls
