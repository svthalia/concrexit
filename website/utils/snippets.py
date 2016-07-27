from django.utils import timezone


def datetime_to_lectureyear(date):
    sept_1 = timezone.make_aware(timezone.datetime(2016, 9, 1))
    if date.date() < sept_1.date():
        return date.year - 1
    return date.year
