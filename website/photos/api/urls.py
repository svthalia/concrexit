from rest_framework import routers

from photos.api import viewsets

router = routers.SimpleRouter()
router.register(r'photos/images', viewsets.PhotosViewSet)
router.register(r'photos/albums', viewsets.AlbumsViewSet)
urlpatterns = router.urls
