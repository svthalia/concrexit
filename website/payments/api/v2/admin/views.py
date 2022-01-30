import rest_framework.filters as framework_filters
from django.apps import apps
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from payments import services, payables, NotRegistered
from payments.api.v2 import filters
from payments.api.v2.admin.serializers.payable_create import (
    PayableCreateAdminSerializer,
)
from payments.api.v2.admin.serializers.payable_detail import PayableAdminSerializer
from payments.api.v2.admin.serializers.payment import (
    PaymentAdminSerializer,
    PaymentCreateSerializer,
)
from payments.exceptions import PaymentError
from payments.models import Payment, PaymentUser
from thaliawebsite.api.v2.admin import (
    AdminListAPIView,
    AdminCreateAPIView,
    AdminRetrieveAPIView,
    AdminDestroyAPIView,
)


class PaymentListCreateView(AdminListAPIView, AdminCreateAPIView):
    """View that allows you to create and list payments as admin."""

    queryset = Payment.objects.prefetch_related(
        "paid_by__profile",
        "paid_by__membership_set",
        "processed_by__profile",
        "processed_by__membership_set",
    )

    required_scopes = ["payments:admin"]
    filter_backends = (
        framework_filters.OrderingFilter,
        filters.CreatedAtFilter,
        filters.PaymentTypeFilter,
    )
    ordering_fields = ("created_at",)

    def get_serializer_class(self):
        if self.request.method.lower() == "post":
            return PaymentCreateSerializer
        return PaymentAdminSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            PaymentAdminSerializer(
                serializer.instance, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(AdminRetrieveAPIView, AdminDestroyAPIView):
    """View that allows you to manage a single payment as admin."""

    queryset = Payment.objects.all()
    serializer_class = PaymentAdminSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["payments:admin"]

    def delete(self, request, *args, **kwargs):
        if self.get_object().batch and self.get_object().batch.processed:
            raise PermissionDenied("This payment cannot be deleted.")
        return super().delete(request, *args, **kwargs)


class PayableDetailView(APIView):
    """View that allows you to manipulate the payment for the payable.

    Permissions of this view are based on the payable.
    """

    required_scopes = ["payments:admin"]
    permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

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
                {api_settings.NON_FIELD_ERRORS_KEY: [_("Payable model not found")]}
            ) from e

        if not payable.can_manage_payment(self.request.member):
            raise PermissionDenied(
                detail=_("You do not have permission to perform this action.")
            )

        return payable

    def get(self, request, *args, **kwargs):
        """Get information about a payable."""
        serializer = PayableAdminSerializer(
            self.get_payable(), context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Remove the current payment for a payable."""
        payable = self.get_payable()

        if not payable.model.payment:
            raise Http404

        try:
            services.delete_payment(
                payable.model,
                request.member,
            )
            payable.model.save()
        except PaymentError as e:
            raise PermissionDenied(detail=str(e))

        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, *args, **kwargs):
        """Mark the payable as paid by creating a payment for it."""
        serializer = PayableCreateAdminSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        payable = self.get_payable()

        try:
            services.create_payment(
                payable,
                PaymentUser.objects.get(pk=request.user.pk),
                serializer.data["payment_type"],
            )
            payable.model.save()
        except PaymentError as e:
            raise ValidationError(detail={api_settings.NON_FIELD_ERRORS_KEY: [str(e)]})

        return Response(
            PayableAdminSerializer(payable, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
