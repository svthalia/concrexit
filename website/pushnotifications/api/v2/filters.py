from rest_framework.filters import BaseFilterBackend


class CategoryFilter(BaseFilterBackend):
    """
    Filter that allows
    """

    def filter_queryset(self, request, queryset, view):
        category = request.query_params.get("category", None)
        if category is not None:
            return queryset.filter(category=category)
        return queryset
