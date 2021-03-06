"""Defines the API routes of the payments package."""
from rest_framework import routers

from payments.api.v1 import viewsets

router = routers.SimpleRouter()
router.register(r"payments", viewsets.PaymentViewset)
urlpatterns = router.urls
