from members.models import Member


class MemberMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.member = Member.objects.get(pk=request.user.pk)
        except Member.DoesNotExist:
            request.member = None

        return self.get_response(request)
