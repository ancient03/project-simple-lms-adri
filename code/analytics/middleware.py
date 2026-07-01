# analytics/middleware.py

from .mongo_service import log_activity


class ActivityLoggingMiddleware:
    """Middleware untuk mencatat aktivitas API ke MongoDB secara otomatis."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Hanya log untuk authenticated users dan API requests
        if (request.user.is_authenticated
                and request.path.startswith('/api/')
                and response.status_code < 400):
            try:
                log_activity(
                    user_id=request.user.id,
                    action=f"{request.method} {request.path}",
                    metadata={
                        "status_code": response.status_code,
                        "ip": request.META.get('REMOTE_ADDR'),
                        "user_agent": request.META.get('HTTP_USER_AGENT', '')[:200]
                    }
                )
            except Exception:
                pass  # Jangan gagalkan request jika logging error

        return response
