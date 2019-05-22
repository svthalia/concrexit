from django.conf.urls import url

from . import views

app_name = "pizzas"

urlpatterns = [
    url(r'^order/cancel$', views.cancel_order, name='cancel-order'),
    url(r'^order/$', views.order, name='order'),
    url(r'^$', views.index, name='index'),
]
