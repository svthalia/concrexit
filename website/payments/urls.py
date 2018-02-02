from django.urls import path

from .views import PaymentAdminView

app_name = 'payments'

urlpatterns = [
    path('admin/process/<uuid:pk>/<type>/',
         PaymentAdminView.as_view(), name='admin-process'),
]
