from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from hashlib import sha256


class Token(models.Model):
    """This class contains an authentication token for an user
    An user may have multiple tokens"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    token = models.CharField(max_length=64)

    @classmethod
    def create_token(cls, user):
        # Post quantum approved
        token = get_random_string(length=64)
        hashed_token = sha256(
            ''.join([user.username, token]).encode()).hexdigest()
        t = cls(user=user, token=hashed_token)
        t.save()
        return token

    @classmethod
    def authenticate(cls, username, token):
        hashed_token = sha256(''.join([username, token]).encode()).hexdigest()
        try:
            user = User.objects.get(username=username,
                                    token__token=hashed_token)
        except User.DoesNotExist:
            return None
        return user
