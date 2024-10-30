from django.urls import path

from .views import ShortLinkView

app_name = "shortlink"

urlpatterns = [
    path("<slug:slug>/", ShortLinkView.as_view(), name="url"),
]
