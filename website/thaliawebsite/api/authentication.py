from rest_framework.authentication import TokenAuthentication


class APIv1TokenAuthentication(TokenAuthentication):
    """Custom token authentication class that only works for API v1"""

    def authenticate(self, request):
        if request.version == "v2":
            return None
        return super().authenticate(request)
