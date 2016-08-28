from rest_framework import routers

from events.api import viewsets

router = routers.SimpleRouter()
router.register(r'events', viewsets.EventViewset)
urlpatterns = router.urls
