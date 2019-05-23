"""The routes defined by the documents package"""
from django.urls import path, include

from . import views

app_name = "documents"

urlpatterns = [
    path('documents/', include([
        path('document/<int:pk>/',
             views.DocumentDownloadView.as_view(), name='document'),
        path('',
             views.DocumentsIndexView.as_view(), name='index'),
    ]))
]
