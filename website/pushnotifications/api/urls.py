from rest_framework import routers

from pushnotifications.api import viewsets

router = routers.SimpleRouter()
router.register(r'devices', viewsets.DeviceViewSet)
router.register(r'notifications', viewsets.MessageViewSet)
urlpatterns = router.urls
