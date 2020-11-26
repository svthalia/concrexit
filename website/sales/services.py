from django.utils import timezone


def is_adult(member):
    today = timezone.now().date()
    return member.profile.birthday <= today.replace(year=today.year - 18)
