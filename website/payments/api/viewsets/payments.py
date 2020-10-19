from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from payments.api.serializers import PaymentSerializer
from payments.models import Payment


class PaymentViewset(ModelViewSet):

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(paid_by=user)
