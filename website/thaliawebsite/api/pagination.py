from rest_framework.pagination import LimitOffsetPagination


class APIv2LimitOffsetPagination(LimitOffsetPagination):
    """Pagination class that uses LimitOffsetPagination and sets the default value for the pagination size to None for API v1."""

    def get_limit(self, request):
        if self.limit_query_param in request.query_params:
            return super().get_limit(request)

        if request.version == "v1":
            return None
        return self.default_limit
