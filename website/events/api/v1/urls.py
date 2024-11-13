from rest_framework import routers

from events.api.v1 import viewsets

router = routers.SimpleRouter()
router.register(r"events", viewsets.EventViewset)
router.register(r"registrations", viewsets.EventRegistrationViewSet)
urlpatterns = router.urls
