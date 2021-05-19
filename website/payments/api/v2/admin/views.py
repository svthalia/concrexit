import rest_framework.filters as framework_filters
from django.apps import apps
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.settings import api_settings

from payments import services, payables, NotRegistered
from payments.api.v2 import filters
from payments.api.v2.admin.serializers.payable_create import PayableCreateSerializer
from payments.api.v2.admin.serializers.payable_detail import PayableSerializer
from payments.api.v2.admin.serializers.payment import (
    PaymentSerializer,
    PaymentCreateSerializer,
)
from payments.exceptions import PaymentError
from payments.models import Payment, PaymentUser
from thaliawebsite.api.v2.admin import (
    AdminListAPIView,
    AdminCreateAPIView,
    AdminRetrieveAPIView,
    AdminDestroyAPIView,
    AdminUpdateAPIView,
)


class PaymentListCreateView(AdminListAPIView, AdminCreateAPIView):
    queryset = Payment.objects.all()

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
        return PaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            PaymentSerializer(
                serializer.instance, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(AdminRetrieveAPIView, AdminDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["payments:admin"]


class PayableBaseView:
    required_scopes = ["payments:admin"]

    def get_permissions(self):
        return [IsAuthenticatedOrTokenHasScope()]

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


class PayableDetailView(
    PayableBaseView, AdminRetrieveAPIView, AdminUpdateAPIView, AdminDestroyAPIView
):
    """View that allows you to manipulate the payment for the payable. Permissions of this view are based on the payable."""

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method.lower() in ["put", "patch"]:
            return PayableCreateSerializer
        return PayableSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_payable())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        payable = self.get_payable()

        if not payable.model.payment:
            raise Http404

        try:
            services.delete_payment(
                payable.model, request.member,
            )
            payable.model.save()
        except PaymentError as e:
            raise PermissionDenied(detail=str(e))

        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
            PayableSerializer(payable, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
