"""Defines the middleware of the thaliawebsite package"""
from rest_framework.authtoken.models import Token


class TokenMiddleware:
    """
    Adds a piece of middleware to Django
    that allows the user to authenticate using the Django Rest Framework
    Token in the HTTP Authorization header.

    You could use it to open a private thumbnail without
    having a session, for example.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META.get('HTTP_AUTHORIZATION'):
            key = request.META.get('HTTP_AUTHORIZATION')[6:]
            try:
                token_obj = Token.objects.get(key=key)
                request.user = token_obj.user
            except Token.DoesNotExist:
                pass
        return self.get_response(request)
