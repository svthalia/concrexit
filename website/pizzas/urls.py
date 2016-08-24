from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^delete-order/$', views.delete_order, name='delete-order'),
    url(r'^add-order/(?P<event_pk>\d+)/$', views.add_order, name='add-order'),
    url(r'^toggle-orderpayment/$', views.toggle_orderpayment, name='toggle-orderpayment'),
    url(r'^cancel-order/$', views.cancel_order, name='cancel-order'),
    url(r'^order/$', views.order, name='order'),
    url(r'^orders/(?P<event_pk>\d+)/$', views.orders, name='orders'),
    url(r'^$', views.index, name='index'),
]
