import rest_framework.filters as framework_filters
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from rest_framework import status, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework.settings import api_settings

from payments import services, payables, NotRegistered
from payments.api.v2 import filters
from payments.api.v2.serializers import PaymentSerializer
from payments.api.v2.serializers.payable_detail import PayableSerializer
from payments.api.v2.serializers.payment_user import PaymentUserSerializer
from payments.exceptions import PaymentError
from payments.models import Payment, PaymentUser
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod
from thaliawebsite.api.v2.serializers import EmptySerializer


class PaymentListView(ListAPIView):
    """Returns an overview of all an authenticated user's payments."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_per_method = {"GET": ["payments:read"]}
    filter_backends = (
        framework_filters.OrderingFilter,
        filters.CreatedAtFilter,
        filters.PaymentTypeFilter,
    )
    ordering_fields = ("created_at",)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(paid_by=PaymentUser.objects.get(pk=self.request.member.pk))
        )


class PaymentDetailView(RetrieveAPIView):
    """Returns a single payment made by the authenticated user."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_per_method = {"GET": ["payments:read"]}

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(paid_by=PaymentUser.objects.get(pk=self.request.member.pk))
        )


class PayableDetailView(RetrieveAPIView):
    """Allow you to get information about a payable and process it."""

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_per_method = {
        "GET": ["payments:read"],
        "PATCH": ["payments:write"],
    }

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method.lower() == "patch":
            return EmptySerializer
        return PayableSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_payable())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_payable(self):
        app_label = self.kwargs["app_label"]
        model_name = self.kwargs["model_name"]
        payable_pk = self.kwargs["payable_pk"]

        try:
            payable_model = apps.get_model(app_label=app_label, model_name=model_name)
            payable = payables.get_payable(
                get_object_or_404(payable_model, pk=payable_pk)
            )
        except (LookupError, NotRegistered) as e:
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [_("Payable model not found.")]}
            ) from e

        if (
            not payable.payment_payer
            or not payable.tpay_allowed
            or payable.payment_payer != PaymentUser.objects.get(pk=self.request.user.pk)
        ):
            raise PermissionDenied(
                detail=_("You do not have permission to perform this action.")
            )

        return payable

    def patch(self, request, *args, **kwargs):
        payable = self.get_payable()

        if payable.payment:
            return Response(
                data={"detail": _("This object has already been paid for.")},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            services.create_payment(
                payable,
                PaymentUser.objects.get(pk=request.user.pk),
                Payment.TPAY,
            )
            payable.model.save()
        except PaymentError as e:
            raise ValidationError(detail={api_settings.NON_FIELD_ERRORS_KEY: [str(e)]})

        return Response(
            PayableSerializer(payable, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentUserCurrentView(RetrieveAPIView):
    """Returns details of the authenticated member."""

    queryset = PaymentUser
    serializer_class = PaymentUserSerializer
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
    ]

    required_scopes_per_method = {"GET": ["payments:read"]}

    def get_object(self):
        return get_object_or_404(PaymentUser, pk=self.request.user.pk)
