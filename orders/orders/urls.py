# orders/urls.py

from django.contrib import admin
from django.urls import path, include
from backend.views import trigger_import

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('backend.urls')), # Подключаем маршруты нашего API
    path('api/admin/trigger-import/', trigger_import, name='trigger_import'),
]