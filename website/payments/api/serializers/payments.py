from rest_framework.serializers import ModelSerializer

from payments.models import Payment


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = ['pk', 'get_type_display', 'amount', 'created_at', 'topic', 'notes']
