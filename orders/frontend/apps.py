from django.apps import AppConfig


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