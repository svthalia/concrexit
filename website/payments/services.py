"""The services defined by the payments package"""
from .models import Payment


def process_payment(queryset, processed_by, pay_type=Payment.CARD):
    """
    Process the payment

    :param queryset: Queryset of payments that should be processed
    :type queryset: QuerySet[Payment]
    :param processed_by: Member that processed this payment
    :type processed_by: Member
    :param pay_type: Type of the payment
    :type pay_type: String
    """

    queryset = queryset.filter(type=Payment.NONE)
    data = []

    # This should trigger post_save signals, thus a queryset update
    # is not appropriate, moreover save() automatically sets
    # the processing date
    for payment in queryset:
        payment.type = pay_type
        payment.processed_by = processed_by
        payment.save()

        data.append(payment)

    return data
