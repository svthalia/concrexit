from django.urls import path
from rest_framework import routers

from members.api import viewsets, views

router = routers.SimpleRouter()
router.register(r'members', viewsets.MemberViewset)
urlpatterns = router.urls + [
    path('sentry-access/', views.SentryIdentityView.as_view()),
]
