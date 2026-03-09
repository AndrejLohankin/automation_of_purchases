# Проект автоматизации закупок

## О проекте

Проект представляет собой систему автоматизации закупок для B2B-клиентов с возможностью импорта товаров из YAML-файлов, управления заказами и интеграции с внешними API.

## Возможности

- ✅ REST API на Django REST Framework
- ✅ Интерактивная документация Swagger UI
- ✅ Импорт товаров из YAML файлов
- ✅ Экспорт товаров в YAML формат
- ✅ Управление корзиной и заказами
- ✅ Отправка email через Celery
- ✅ Ограничение частоты запросов (Throttling)
- ✅ Тесты с покрытием кода
- ✅ Социальная авторизация (Google)
- ✅ Улучшенная админка (Baton Theme)
- ✅ Асинхронная обработка изображений товаров (Easy Thumbnails)
- ✅ Мониторинг ошибок (Sentry)
- ✅ Кэширование запросов к БД (django-cachalot + Redis)

## Быстрый запуск

### 1. Запуск через Docker

```bash
# Сборка и запуск контейнеров
docker-compose up -d --build

# Остановка контейнеров
docker-compose down
```

### 2. Первоначальная настройка

После первого запуска необходимо выполнить миграции:

```bash
# Войти в контейнер
docker-compose exec django bash

# Выполнить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser
```

## API документация

### Swagger UI

После запуска контейнеров интерактивная документация API доступна по адресам:

- **Swagger UI**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

В Swagger UI вы можете:
- Просмотреть все доступные endpoints
- Тестировать API прямо из браузера (кнопка "Try it out")
- Видеть схемы запросов и ответов

### Основные endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/v1/register/` | Регистрация пользователя |
| POST | `/api/v1/login/` | Вход пользователя |
| GET | `/api/v1/products/` | Список товаров |
| GET/POST/PUT/DELETE | `/api/v1/basket/` | Управление корзиной |
| POST | `/api/v1/contacts/` | Добавить контакт |
| POST | `/api/v1/orders/confirm/` | Подтвердить заказ |
| GET | `/api/v1/orders/history/` | История заказов |
| PUT | `/api/v1/orders/{id}/status/` | Обновить статус заказа (админ) |

### Throttling (ограничение частоты запросов)

API защищено от злоупотреблений с помощью throttling:

- **Анонимные пользователи**: 100 запросов в минуту
- **Авторизованные пользователи**: 1000 запросов в минуту

При превышении лимита возвращается код 429 Too Many Requests.

## Социальная авторизация

Проект поддерживает вход через Google и Telegram.

### Настройка ключей

Для работы социальной авторизации необходимо получить ключи от провайдеров.

#### Google OAuth 2.0

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект
3. Перейдите в **APIs & Services** → **Credentials**
4. Нажмите **Create Credentials** → **OAuth client ID**
5. Выберите **Web application**
6. Заполните:
   - **Name**: Orders API
   - **Authorized JavaScript origins**: 
     ```
     http://localhost:8000
     ```
   - **Authorized redirect URIs**:
     ```
     http://localhost:8000/auth/complete/google-oauth2/
     ```
7. Скопируйте **Client ID** и **Client Secret**


### Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Копировать пример
cp .env.example .env
```

Заполните `.env` полученными ключами:

```env
# Social Auth - Google
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-client-id.apps.googleusercontent.com
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-client-secret

# Social Auth - Telegram
SOCIAL_AUTH_TELEGRAM_BOT_TOKEN=your-bot-token
```

Перезапустите контейнеры:

```bash
docker-compose down
docker-compose up -d --build
```

### Тестирование

После настройки ключей:
1. Откройте http://localhost:8000/login/
2. Нажмите кнопку "Google"
3. Авторизуйтесь через выбранный сервис

## Админка (Baton Theme)

Проект использует современную тему админки **Baton** с дополнительными функциями:

### Возможности Baton

- Современный дизайн с Material Symbols
- Настраиваемое боковое меню
- Тёмная/светлая тема
- Поддержка переводов (AI функции)
- Адаптивный дизайн для мобильных устройств
- Улучшенные списки с фильтрами в модальных окнах

## Асинхронная обработка изображений

Проект поддерживает автоматическое создание миниатюр изображений товаров с использованием **Easy Thumbnails** и **Celery**.

### Доступные размеры миниатюр

- **Small**: 64x64 (обрезка по центру)
- **Medium**: 150x150 (обрезка по центру)
- **Large**: 300x300 (обрезка по центру)

### API Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/v1/products/upload/` | Загрузить изображение товара |
| POST | `/api/v1/products/batch-upload/` | Пакетная загрузка изображений |

### Загрузка изображения по URL

```bash
# Загрузка изображения по URL (асинхронная)
curl -X POST http://localhost:8000/api/v1/products/upload/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "image_url": "https://example.com/image.jpg"}'
```

Ответ:
```json
{
  "message": "Изображение будет загружено асинхронно",
  "task_id": "abc123",
  "product_id": 1
}
```

### Загрузка файла

```bash
# Загрузка файла изображения
curl -X POST http://localhost:8000/api/v1/products/upload/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "product_id=1" \
  -F "image=@/path/to/image.jpg"
```

### Пакетная загрузка

```bash
# Пакетная загрузка изображений
curl -X POST http://localhost:8000/api/v1/products/batch-upload/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {"product_id": 1, "image_url": "https://example.com/1.jpg"},
      {"product_id": 2, "image_url": "https://example.com/2.jpg"}
    ]
  }'
```

### Ответ API с миниатюрами

При получении списка товаров теперь возвращаются URL миниатюр:

```json
{
  "id": 1,
  "product": {
    "id": 1,
    "name": "Смартфон",
    "image_original": "/media/products/2024/01/01/image.jpg",
    "image_small": "/media/products/2024/01/01/image.64x64.jpg",
    "image_medium": "/media/products/2024/01/01/image.150x150.jpg",
    "image_large": "/media/products/2024/01/01/image.300x300.jpg"
  }
}
```

### Удаление старых изображений

Для очистки старых неиспользуемых изображений запустите задачу:

```python
from backend.tasks import cleanup_old_images
cleanup_old_images.delay(days=30)  # Удалить изображения старше 30 дней
```

## Мониторинг ошибок (Sentry)

Проект интегрирован с **Sentry** для отслеживания ошибок и мониторинга производительности.

### Возможности Sentry

- Автоматический сбор исключений Django
- Интеграция с Celery для отслеживания ошибок в фоновых задачах
- Трассировка запросов (traces)
- Детальная информация об ошибках с контекстом
- Уведомления об ошибках

### Настройка Sentry

1. Зарегистрируйтесь на [sentry.io](https://sentry.io)
2. Создайте новый проект для Django
3. Скопируйте **DSN** из настроек проекта
4. Добавьте DSN в файл `.env`:

```env
# Sentry
SENTRY_DSN=https://example@sentry.io/1234567
```

5. Перезапустите контейнеры:

```bash
docker-compose down
docker-compose up -d --build
```

**Примечание:** Переменная `SENTRY_DSN` автоматически передаётся в контейнеры через `docker-compose.yml`.

### API Endpoint для тестирования

```bash
# Тестовый endpoint для проверки Sentry
curl -X GET http://localhost:8000/api/v1/sentry-test/ \
  -H "Authorization: Token YOUR_ADMIN_TOKEN"
```

Ответ (с кодом 500):
```json
{
  "message": "Тестовая ошибка отправлена в Sentry",
  "sentry_status": "enabled",
  "error": "Тестовая ошибка Sentry!"
}
```

После вызова вы увидите ошибку в панели Sentry:
- **Level**: Error
- **Message**: Тестовая ошибка Sentry!
- **Environment**: development (или production)
- **Release**: orders@1.0.0

## Кэширование запросов к БД

Проект использует **django-cachalot** с Redis для автоматического кэширования запросов к базе данных.

### Возможности

- Автоматическое кэширование ORM-запросов
- Инвалидация кэша при изменениях в БД
- Использование Redis для хранения кэша
- Значительное уменьшение времени отклика при повторных запросах

### Как это работает

1. При первом запросе данные загружаются из БД и сохраняются в Redis
2. При повторном запросе данные берутся из кэша (0 запросов к БД)
3. При изменении данных (POST/PUT/DELETE) кэш автоматически инвалидируется

### Тестирование производительности

```bash
# Тестовый endpoint показывает:
# - количество запросов к БД
# - время выполнения
# - информацию о кэше

curl http://localhost:8000/api/v1/cache-test/
```

Пример ответа:
```json
{
  "message": "Тест производительности кэширования",
  "results": {
    "products_count": 10,
    "query_count": 0,
    "execution_time_ms": 2.5,
    "cache": {
      "cache_backend": "RedisCache",
      "cache_enabled": true
    }
  },
  "note": "При повторном запросе количество запросов к БД должно быть 0"
}
```

### Настройка кэша

По умолчанию используется Redis с базой данных 1 (отдельная от Celery). Настройки в `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('CACHE_URL', 'redis://redis:6379/1'),
        'KEY_PREFIX': 'orders',
        'TIMEOUT': 300,
    }
}

# Настройки cachalot
CACHALOT_ENABLED = True
CACHALOT_TIMEOUT = 60
CACHALOT_CACHE = 'default'
```

Также добавьте переменную `CACHE_URL` в `.env`:

```env
# Redis
CACHE_URL=redis://redis:6379/1
```

### Доступ к админке

- **URL**: http://localhost:8000/admin/
- **Логин**: созданный при `createsuperuser`

### Настройка темы

Тема активирована по умолчанию. Для настройки:

1. Перейдите в **Baton** → **Admin themes**
2. Отредактируйте тему "baton"
3. Настройте параметры:
   - `SITE_TITLE`: "Orders Admin"
   - `SITE_HEADER`: "Автоматизация закупок"
   - `MENU_COLLAPSED`: сворачиваемое меню
   - и другие опции

## Тестирование

### Запуск тестов

```bash
# Запуск всех тестов
docker-compose exec django python manage.py test

# Запуск тестов с покрытием кода
docker-compose exec django coverage run manage.py test
docker-compose exec django coverage report --include="*views.py"
# Отдельный TestCase для DRF throttling
docker-compose exec django python manage.py test backend.test_api.ThrottlingTestCase -v 2
```

### Результаты тестирования

- **Количество тестов**: 55
- **Покрытие кода views.py**: 66%

## Структура проекта

```
orders/
├── backend/           # Backend API
│   ├── views.py       # API Views
│   ├── serializers.py # DRF Serializers
│   ├── models.py      # Django Models
│   ├── tasks.py       # Celery задачи
│   └── test_api.py    # Тесты API
├── frontend/          # Frontend приложение
├── orders/            # Django проект
│   └── settings.py    # Настройки
└── data/              # YAML файлы для импорта
```

- **Кэширование**: django-cachalot + Redis

- **Backend**: Django REST Framework
- **Frontend**: Django Templates
- **База данных**: SQLite (development) / PostgreSQL (production)
- **Очереди**: Celery + Redis
- **Контейнеризация**: Docker
- **Документация**: DRF-Spectacular (Swagger UI)
- **Админка**: Baton Theme
- **Тестирование**: Django Test Framework + Coverage

## Устранение проблем

### Контейнер не запускается

```bash
docker-compose logs django
docker-compose logs redis
```

### Проблемы с миграциями

```bash
docker-compose exec django python manage.py showmigrations
docker-compose exec django python manage.py migrate
```

### Проблемы с Celery

```bash
docker-compose logs celery_worker
```

## Контакты

https://github.com/AndrejLohankin/automation_of_purchases

*Документация актуальна на 2026 год*
