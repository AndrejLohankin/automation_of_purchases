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

## Тестирование

### Запуск тестов

```bash
# Запуск всех тестов
docker-compose exec django python manage.py test

# Запуск тестов с покрытием кода
docker-compose exec django coverage run manage.py test
docker-compose exec django coverage report --include="*views.py"
```

### Результаты тестирования

- **Количество тестов**: 32
- **Покрытие кода views.py**: 65%

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

## Технологический стек

- **Backend**: Django REST Framework
- **Frontend**: Django Templates
- **База данных**: SQLite (development) / PostgreSQL (production)
- **Очереди**: Celery + Redis
- **Контейнеризация**: Docker
- **Документация**: DRF-Spectacular (Swagger UI)
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
