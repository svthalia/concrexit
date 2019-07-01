"""The routes defined by the activemembers package"""
from django.urls import path, re_path

from activemembers.views import (
    CommitteeIndexView, CommitteeDetailView,
    SocietyIndexView, SocietyDetailView,
    BoardIndexView, BoardDetailView
)

app_name = "activemembers"

urlpatterns = [
    path('committees/',
         CommitteeIndexView.as_view(), name='committees'),
    path('committees/<int:pk>/',
         CommitteeDetailView.as_view(), name='committee'),
    path('societies/',
         SocietyIndexView.as_view(), name='societies'),
    path('societies/<int:pk>/',
         SocietyDetailView.as_view(), name='society'),
    path('boards/',
         BoardIndexView.as_view(), name='boards'),
    re_path(r'boards/(?P<since>\d{4})-(?P<until>\d{4})/$',
            BoardDetailView.as_view(), name='board'),
]
