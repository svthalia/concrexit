from .models import Payment


def process_payment(queryset, pay_type=Payment.CARD):
    """
        Process the payment

        :param queryset: Queryset of payments that should be processed
        :type queryset: QuerySet[Payment]
        :param pay_type: Type of the payment
        :type pay_type: String
        """

    queryset = queryset.filter(processed=False)
    data = []

    # This should trigger post_save signals, thus a queryset update
    # is not appropriate, moreover save() automatically sets
    # the processing date
    for payment in queryset:
        payment.processed = True
        payment.type = pay_type
        payment.save()

        data.append(payment)

    return data
