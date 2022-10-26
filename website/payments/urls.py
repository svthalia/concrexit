from django.urls import include, path

from .views import (
    BankAccountCreateView,
    BankAccountListView,
    BankAccountRevokeView,
    PaymentListView,
    PaymentProcessView,
)

app_name = "payments"

urlpatterns = [
    path(
        "user/finance/",
        include(
            [
                path(
                    "accounts/",
                    include(
                        [
                            path(
                                "",
                                BankAccountListView.as_view(),
                                name="bankaccount-list",
                            ),
                            path(
                                "add/",
                                BankAccountCreateView.as_view(),
                                name="bankaccount-add",
                            ),
                            path(
                                "<uuid:pk>/revoke/",
                                BankAccountRevokeView.as_view(),
                                name="bankaccount-revoke",
                            ),
                        ]
                    ),
                ),
                path(
                    "payments/",
                    include(
                        [
                            path("", PaymentListView.as_view(), name="payment-list"),
                            path(
                                "<int:year>-<int:month>/",
                                PaymentListView.as_view(),
                                name="payment-list",
                            ),
                            path(
                                "process/",
                                PaymentProcessView.as_view(),
                                name="payment-process",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
