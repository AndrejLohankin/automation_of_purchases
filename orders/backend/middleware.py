# backend/middleware.py

from django.utils.deprecation import MiddlewareMixin

class DisableCSRFForAPIMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/api/v1/'):
            setattr(request, '_dont_enforce_csrf_checks', True)