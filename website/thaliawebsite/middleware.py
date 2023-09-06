class RealIPMiddleware:
    """Sets `REMOTE_ADDR` to the X-Real-IP header set by the reverse proxy."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "X-Real-Ip" in request.headers:
            request.META["REMOTE_ADDR"] = request.headers["X-Real-Ip"]
        return self.get_response(request)
