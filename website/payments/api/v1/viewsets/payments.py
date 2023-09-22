from django.apps import apps
from django.urls import reverse

from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from payments import services
from payments.api.v1.serializers import PaymentCreateSerializer, PaymentSerializer
from payments.exceptions import PaymentError
from payments.models import Payment, PaymentUser
from payments.payables import payables


class PaymentViewset(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """The viewset to list retrieve and create payments."""

    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(paid_by=user)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app_label = serializer.data["app_label"]
        model_name = serializer.data["model_name"]
        payable_pk = serializer.data["payable_pk"]

        payable_model = apps.get_model(app_label=app_label, model_name=model_name)
        payable = payables.get_payable(payable_model.objects.get(pk=payable_pk))

        if (
            payable.payment_payer.pk
            != PaymentUser.objects.get(pk=self.request.user.pk).pk
        ):
            raise PermissionDenied(
                detail="You are not allowed to process this payment."
            )

        if payable.payment:
            return Response(
                data={"detail": "This object has already been paid for."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            services.create_payment(
                payable,
                PaymentUser.objects.get(pk=request.user.pk),
                Payment.TPAY,
            )
        except PaymentError as e:
            raise ValidationError(detail=str(e)) from e

        payable.model.refresh_from_db()
        headers = {
            "Location": reverse(
                "api:v1:payment-detail", kwargs={"pk": payable.payment.pk}
            )
        }
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
