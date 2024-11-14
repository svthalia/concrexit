from rest_framework.pagination import LimitOffsetPagination


class APIv2LimitOffsetPagination(LimitOffsetPagination):
    """Pagination class that uses LimitOffsetPagination."""

    def get_limit(self, request):
        if self.limit_query_param in request.query_params:
            return super().get_limit(request)

        return self.default_limit
