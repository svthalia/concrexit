from django.urls import path

from . import views

app_name = "moneybird"

urlpatterns = [
    path("webhook_receive/", views.webhook_receive, name="webhook_receive"),
]
