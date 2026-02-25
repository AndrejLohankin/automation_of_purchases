#!/usr/bin/env python
"""
Утилита управления для frontend приложения.

Эта утилита предоставляет команды для управления Django приложением,
такие как запуск сервера, создание миграций, создание суперпользователя и т.д.
"""

import os
import sys

def main():
    """Основная функция для запуска Django утилиты."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frontend.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()