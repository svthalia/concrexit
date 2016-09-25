from rest_framework import routers

from partners.api import viewsets

router = routers.SimpleRouter()
router.register(r'partners', viewsets.PartnerViewset)
urlpatterns = router.urls
