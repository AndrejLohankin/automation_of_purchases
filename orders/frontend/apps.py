from django.apps import AppConfig
from django.conf import settings


class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend'
    verbose_name = 'Frontend'

    def ready(self):
        # Импортируем сигналы, если они есть
        import frontend.signals  # noqa

        # Импортируем менеджеры, если они есть
        import frontend.managers  # noqa

        # Импортируем admin, если нужно
        import frontend.admin  # noqa

        # Другие инициализации при загрузке приложения
        # ...
        pass

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