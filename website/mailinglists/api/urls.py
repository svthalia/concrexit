from rest_framework import routers

from mailinglists.api import viewsets

router = routers.SimpleRouter()
router.register(r'mailinglists', viewsets.MailingListViewset)
urlpatterns = router.urls
