from django.urls import path, include

from .views import BankAccountCreateView, BankAccountListView, \
    BankAccountRevokeView

app_name = 'payments'

urlpatterns = [
    # path('', views.index, name='index'),
    path('accounts/', include([
        path('', BankAccountListView.as_view(),
             name='bankaccount-list'),
        path('add/', BankAccountCreateView.as_view(),
             name='bankaccount-add'),
        path('<uuid:pk>/revoke/', BankAccountRevokeView.as_view(),
             name='bankaccount-revoke'),
    ])),
]
