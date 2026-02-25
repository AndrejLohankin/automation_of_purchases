# Настройки для frontend приложения

from django.conf import settings

# URL для API
API_BASE_URL = f'http://{settings.ALLOWED_HOSTS[0]}/api/v1/' if settings.ALLOWED_HOSTS else 'http://localhost:8000/api/v1/'

# Настройки для изображений
IMAGE_MAX_SIZE = 5 * 1024 * 1024  # 5MB
IMAGE_ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

# Настройки для кэширования
CACHE_TTL = 3600  # 1 час

# Настройки для пагинации
ITEMS_PER_PAGE = 12

# Настройки для уведомлений
NOTIFICATION_TIMEOUT = 5000  # 5 секунд

# Настройки для валидации форм
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Настройки для файлов
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

# Настройки для email
DEFAULT_FROM_EMAIL = 'noreply@automation-of-purchases.local'

# Настройки для логирования
LOG_LEVEL = 'INFO'
LOG_FILE = 'frontend.log'

# Настройки для отладки
DEBUG = settings.DEBUG

# Настройки для CORS (если нужно)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Настройки для безопасности
CSRF_COOKIE_NAME = 'csrftoken_frontend'
SESSION_COOKIE_NAME = 'sessionid_frontend'

# Настройки для интернационализации
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'

# Настройки для тестирования
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Настройки для миграций
MIGRATION_MODULES = {
    'frontend': 'frontend.migrations',
}

# Настройки для статических файлов
STATIC_URL = '/static/frontend/'
STATICFILES_DIRS = [
    settings.BASE_DIR / 'frontend' / 'static',
]
STATIC_ROOT = settings.BASE_DIR / 'static' / 'frontend'

# Настройки для медиафайлов
MEDIA_URL = '/media/frontend/'
MEDIA_ROOT = settings.BASE_DIR / 'media' / 'frontend'

# Настройки для шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [settings.BASE_DIR / 'frontend' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Настройки для middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Настройки для installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'frontend',
]

# Настройки для базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': settings.BASE_DIR / 'db.sqlite3',
    }
}

# Настройки для паролей
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Настройки для интернационализации
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Настройки для статических файлов
STATIC_URL = '/static/frontend/'
STATICFILES_DIRS = [
    settings.BASE_DIR / 'frontend' / 'static',
]
STATIC_ROOT = settings.BASE_DIR / 'static' / 'frontend'

# Настройки для медиафайлов
MEDIA_URL = '/media/frontend/'
MEDIA_ROOT = settings.BASE_DIR / 'media' / 'frontend'

# Настройки для паролей
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Настройки для интернационализации
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Настройки для дебаг тулбара (если установлен)
if settings.DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', '::1']