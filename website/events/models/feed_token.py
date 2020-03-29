from django.db import models
from django.utils.crypto import get_random_string


class FeedToken(models.Model):
    """Used to personalize the ical Feed"""

    member = models.OneToOneField("members.Member", models.CASCADE)
    token = models.CharField(max_length=32, editable=False)

    def save(self, *args, **kwargs):
        self.token = get_random_string(32)
        super().save(*args, **kwargs)

    @staticmethod
    def get_member(token):
        try:
            return FeedToken.objects.get(token=token).member
        except FeedToken.DoesNotExist:
            return None

    def __str__(self):
        return "{} ({})".format(self.member.get_full_name(), self.token)
