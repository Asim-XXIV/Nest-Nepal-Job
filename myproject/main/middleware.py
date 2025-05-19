from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import time
import logging

logger = logging.getLogger(__name__)


class RequestLogMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests and their processing time
    """

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(
                f"{request.method} {request.path} completed in {duration:.2f}s "
                f"with status {response.status_code}"
            )
        return response


class APIExceptionMiddleware(MiddlewareMixin):
    """
    Middleware to handle any unhandled exceptions in the views
    """

    def process_exception(self, request, exception):
        logger.error(f"Unhandled exception: {str(exception)}", exc_info=True)
        return JsonResponse({
            "error": "An unexpected error occurred. Please try again later."
        }, status=500)
