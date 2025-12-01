# api/middleware.py - Custom middleware for error handling and logging
import logging
import time
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('api')


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Global error handling middleware to catch and format exceptions
    """
    def process_exception(self, request, exception):
        logger.error(
            f"Unhandled exception: {str(exception)}",
            exc_info=True,
            extra={
                'path': request.path,
                'method': request.method,
                'user': getattr(request, 'user', None),
            }
        )
        
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(exception) if logger.level == logging.DEBUG else 'An unexpected error occurred',
            'path': request.path,
        }, status=500)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Logs all API requests with timing information
    """
    def process_request(self, request):
        request.start_time = time.time()
        
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Only log API requests
            if request.path.startswith('/api/'):
                logger.info(
                    f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s",
                    extra={
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code,
                        'duration': duration,
                        'user': str(getattr(request, 'user', 'Anonymous')),
                    }
                )
        
        return response


class RequestIDMiddleware(MiddlewareMixin):
    """
    Adds a unique request ID to each request for tracking
    """
    def process_request(self, request):
        import uuid
        request.request_id = str(uuid.uuid4())
        
    def process_response(self, request, response):
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        return response
