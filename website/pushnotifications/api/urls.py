from rest_framework import routers

from pushnotifications.api import viewsets

router = routers.SimpleRouter()
router.register(r'devices', viewsets.DeviceViewSet)
urlpatterns = router.urls
