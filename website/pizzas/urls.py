from django.urls import include, path

from . import views

app_name = "pizzas"

urlpatterns = [
    path(
        "pizzas/",
        include(
            [
                path("order/cancel/", views.cancel_order, name="cancel-order"),
                path("order/", views.place_order, name="order"),
                path("", views.index, name="index"),
            ]
        ),
    ),
]
