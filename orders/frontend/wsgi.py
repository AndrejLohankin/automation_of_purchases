#!/usr/bin/env python
"""
WSGI конфигурация для frontend приложения.

Это модуль WSGI, который предоставляет интерфейс между Django приложением и веб-сервером.
Он используется для запуска Django приложения в продакшене.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application
from django.conf import settings

# Добавляем директорию проекта в Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Задаем переменную окружения для Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frontend.settings')

# Настраиваем frontend для работы с backend
if not settings.configured:
    from django.conf import settings as django_settings

    # Настройки для frontend
    django_settings.ALLOWED_HOSTS = ['*']
    django_settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': django_settings.BASE_DIR / 'db.sqlite3',
        }
    }
    django_settings.AUTH_USER_MODEL = 'backend.User'
    django_settings.INSTALLED_APPS += ['frontend']
    django_settings.MIDDLEWARE += [
        'django.middleware.csrf.CsrfViewMiddleware',
    ]

# Получаем WSGI приложение
application = get_wsgi_application()