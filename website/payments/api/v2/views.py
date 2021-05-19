import rest_framework.filters as framework_filters
from django.apps import apps
from rest_framework.settings import api_settings
from rest_framework import status, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response

from payments import services, payables, NotRegistered
from payments.api.v2 import filters
from payments.api.v2.serializers import PaymentSerializer
from payments.api.v2.serializers.payment_create import PaymentCreateSerializer
from payments.exceptions import PaymentError
from payments.models import Payment, PaymentUser
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class PaymentListCreateView(ListAPIView, RetrieveAPIView, CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_per_method = {
        "GET": ["payments:read"],
        "POST": ["payments:write"],
    }
    filter_backends = (
        framework_filters.OrderingFilter,
        filters.CreatedAtFilter,
        filters.PaymentTypeFilter
    )
    ordering_fields = (
        "created_at",
    )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(paid_by=PaymentUser.objects.get(pk=self.request.member.pk))
        )

    def post(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app_label = serializer.data["app_label"]
        model_name = serializer.data["model_name"]
        payable_pk = serializer.data["payable_pk"]

        try:
            payable_model = apps.get_model(app_label=app_label, model_name=model_name)
            payable = payables.get_payable(get_object_or_404(payable_model, pk=payable_pk))
        except (LookupError, NotRegistered) as e:
            raise serializers.ValidationError({ api_settings.NON_FIELD_ERRORS_KEY: ["Payable model not found"] }) from e

        if (
            not payable.payment_payer or
            payable.payment_payer != PaymentUser.objects.get(pk=self.request.user.pk)
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
            payment = services.create_payment(
                payable, PaymentUser.objects.get(pk=request.user.pk), Payment.TPAY,
            )
            payable.model.save()
        except PaymentError as e:
            raise ValidationError(detail={ api_settings.NON_FIELD_ERRORS_KEY: [str(e)] })

        return Response(
            self.get_serializer(payment).data, status=status.HTTP_201_CREATED
        )

class PaymentDetailView(RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(paid_by=PaymentUser.objects.get(pk=self.request.member.pk))
        )





