import logging

logger = logging.getLogger("django.request")


class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            logger.debug(request)
            logger.debug(request.headers)
            return self.get_response(request)
        except:
            raise  # Raise exception again after catching
