from django.contrib import admin
from django.urls import path, include
from backend.views import trigger_import
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    path('api/v1/', include('backend.urls')), # Подключаем маршруты нашего API
    path('api/admin/trigger-import/', trigger_import, name='trigger_import'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('', include('frontend.urls')), # Добавляем основные URL для frontend
    # Социальная авторизация
    path('auth/', include('social_django.urls', namespace='social')),
]
# Добавляем маршруты для медиа-файлов (изображений товаров)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
