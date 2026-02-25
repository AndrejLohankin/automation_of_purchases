#!/usr/bin/env python
"""
WSGI конфигурация для frontend приложения.

Это модуль WSGI, который предоставляет интерфейс между Django приложением и веб-сервером.
Он используется для запуска Django приложения в продакшене.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Добавляем директорию проекта в Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Задаем переменную окружения для Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frontend.settings')

# Получаем WSGI приложение
application = get_wsgi_application()