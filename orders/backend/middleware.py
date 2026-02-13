# backend/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware

class DisableCSRFForAPIMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Пропускаем CSRF-проверку только для API-эндпоинтов
        if request.path.startswith('/api/v1/'):
            setattr(request, '_dont_enforce_csrf_checks', True)