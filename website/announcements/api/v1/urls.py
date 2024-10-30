from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"announcements/slides", viewsets.SlideViewset)
urlpatterns = router.urls
