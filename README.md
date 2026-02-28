# Проект автоматизации закупок

## О проекте

Проект представляет собой систему автоматизации закупок для B2B-клиентов с возможностью импорта товаров из YAML-файлов, управления заказами и интеграции с внешними API.

## Быстрый запуск

### 1. Запуск через Docker

```bash
# Сборка и запуск контейнеров
cd orders
docker-compose up --build

# Остановка контейнеров
docker-compose down
```

### 2. Первоначальная настройка

После первого запуска необходимо выполнить миграции:

```bash
# Войти в контейнер
docker-compose exec web bash

# Выполнить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser
```

## API документация

### 1. Запуск сервера
После запуска контейнеров API будет доступен по адресу:
- **Frontend**: http://localhost:8000
- **Backend API**: http://localhost:8000/api/

### 2. Использование requests_example.http

Файл `requests_example.http` содержит примеры запросов для тестирования API:

```http
### Регистрация пользователя
POST http://localhost:8000/api/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

### Авторизация пользователя
POST http://localhost:8000/api/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

### Получение списка товаров
GET http://localhost:8000/api/products/
Authorization: Token your_token_here

### Добавление товара в корзину
POST http://localhost:8000/api/basket/
Content-Type: application/json
Authorization: Token your_token_here

{
  "product_info_id": 1,
  "quantity": 1
}

### Подтверждение заказа
POST http://localhost:8000/api/orders/confirm/
Content-Type: application/json
Authorization: Token your_token_here

{
  "basket_id": 1,
  "contact_id": 1
}
```

### 3. Работа с API

1. Откройте файл `requests_example.http` в IDE (например, PyCharm)
2. Запустите нужный запрос
3. Проверьте ответ от сервера
4. Используйте полученный токен для аутентификации в последующих запросах

## Административная панель

### 1. Доступ к админке
- URL: http://localhost:8000/admin/
- Логин: (созданный при настройке для суперпользователя)
- Пароль: (указанный при создании для суперпользователя)

### 2. Управление товарами

#### Импорт товаров из YAML
1. Перейдите в раздел "Импорт товаров"
2. Загрузите YAML-файл (например, shop5.yaml)
3. Нажмите "Запустить импорт через Celery"
4. Дождитесь завершения импорта

#### Экспорт товаров
1. Перейдите в раздел "Информация о продукте"
2. Выберите товары для экспорта
3. Нажмите "Экспорт выбранных товаров"
4. Скачайте сгенерированный YAML-файл

### 3. Управление пользователями

#### Создание пользователей
1. Перейдите в раздел "Пользователи"
2. Нажмите "Добавить пользователя"
3. Заполните данные и сохраните

#### Управление магазинами
1. Перейдите в раздел "Магазины"
2. Добавьте/измените магазины
3. Управляйте доступом к заказам

### 4. Управление заказами

#### Просмотр заказов
1. Перейдите в раздел "Заказы"
2. Фильтруйте по статусу, дате, пользователю
3. Просматривайте детальную информацию

#### Изменение статуса заказа
1. Выберите заказ
2. Нажмите "Изменить"
3. Обновите статус
4. Сохраните изменения

## Структура проекта

```
orders/
├── backend/           # Backend API
├── frontend/          # Frontend приложение
├── orders/            # Django проект
└── imports/           # YAML файлы импорта
```

## Технологический стек

- **Backend**: Django REST Framework
- **Frontend**: Django Templates
- **База данных**: PostgreSQL
- **Очереди**: Celery + Redis
- **Контейнеризация**: Docker
- **Виртуализация**: Docker Compose

## Тестирование

1. Запуск всех тестов:

# Войти в контейнер
docker-compose exec django bash

# Запустить все тесты
python manage.py test

### Проблемы с запуском

1. **Контейнер не запускается**
   ```bash
   docker-compose logs web
   docker-compose logs db
   ```

2. **Проблемы с миграциями**
   ```bash
   docker-compose exec web python manage.py showmigrations
   docker-compose exec web python manage.py migrate --fake
   ```

### Проблемы с импортом

1. **Ошибка формата YAML**
   - Проверьте синтаксис YAML файла
   - Используйте валидатор YAML

2. **Проблемы с Celery**
   ```bash
   docker-compose logs celery
   ```

## Контакты
https://github.com/AndrejLohankin/automation_of_purchases

*Документация актуальна на 2026 год*