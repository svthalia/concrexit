from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"pizzas", viewsets.PizzaViewset)
router.register(r"pizzas/orders", viewsets.OrderViewset)
urlpatterns = router.urls
