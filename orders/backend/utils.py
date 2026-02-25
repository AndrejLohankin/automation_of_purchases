# backend/utils.py

import yaml
from urllib.request import urlopen
from urllib.parse import urlparse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, User
import logging

logger = logging.getLogger(__name__)

def load_data(filepath_or_url, user_id=None):
    """
    Загружает данные из YAML-файла (по пути или URL) в базу данных.
    Может быть вызвана из Django Management Command или API View.

    :param filepath_or_url: Путь к файлу .yaml или URL на YAML-файл
    :param user_id: (Опционально) ID пользователя (владельца магазина), если файл загружается через API
    :return: dict с результатом {'Status': bool, 'Message': str}
    """
    try:
        validator = URLValidator()
        parsed_url = urlparse(filepath_or_url)
        is_url = parsed_url.scheme and parsed_url.netloc

        if is_url:
            try:
                validator(filepath_or_url)
            except ValidationError:
                return {'Status': False, 'Error': 'Некорректный URL.'}

            # Загрузка YAML из URL
            response = urlopen(filepath_or_url)
            data = yaml.safe_load(response)
        else:
            # Загрузка YAML из локального файла
            with open(filepath_or_url, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

        # Проверка структуры YAML
        required_keys = ['shop', 'categories', 'goods']
        for key in required_keys:
            if key not in data:
                return {'Status': False, 'Error': f'Некорректный формат YAML-файла. Отсутствует ключ: {key}.'}

        shop_name = data['shop']
        categories_data = data['categories']
        goods_data = data['goods']

        # Получаем или создаем магазин
        # Если user_id предоставлен (например, из API), связываем его с магазином
        shop_defaults = {'state': True}
        if user_id:
            shop_defaults['user_id'] = user_id

        shop, created = Shop.objects.get_or_create(
            name=shop_name,
            defaults=shop_defaults
        )
        if created:
            logger.info(f"Создан магазин: {shop_name}")
        else:
            logger.info(f"Обновление прайса для магазина: {shop_name}")
            if user_id and shop.user_id != user_id:
                 # Возможно, стоит добавить проверку прав на обновление чужого магазина
                 # или логировать попытку
                 pass # В рамках текущей задачи просто продолжаем

        # Обработка категорий
        for category_data in categories_data:
            category_id = category_data.get('id')
            category_name = category_data.get('name')

            if not category_id or not category_name:
                logger.warning(f"Пропущена категория с некорректными данными: {category_data}")
                continue

            category_obj, _ = Category.objects.get_or_create(
                id=category_id,
                defaults={'name': category_name}
            )
            # Связываем магазин с категорией
            if shop not in category_obj.shops.all():
                category_obj.shops.add(shop)
                logger.debug(f"Магазин {shop.name} добавлен к категории {category_obj.name}")

        # Удаляем старые ProductInfo для этого магазина перед импортом новых
        deleted_count, _ = ProductInfo.objects.filter(shop_id=shop.id).delete()
        logger.info(f"Удалено {deleted_count} старых записей ProductInfo для магазина {shop.name}.")

        # Обработка товаров
        for item in goods_data:
            product_name = item.get('name')
            category_id = item.get('category')
            external_id = item.get('id')
            model_name = item.get('model', '')
            price = item.get('price')
            price_rrc = item.get('price_rrc')
            quantity = item.get('quantity')
            parameters = item.get('parameters', {})

            # Проверяем обязательные поля
            if not all([product_name, category_id, external_id, price, quantity]):
                 logger.error(f"Пропущен товар с некорректными данными: {item}")
                 continue

            # Получаем или создаем Product
            product, _ = Product.objects.get_or_create(
                name=product_name,
                defaults={'category_id': category_id} # Убедитесь, что категория с таким ID существует
            )

            # Создаем или обновляем ProductInfo
            product_info, created = ProductInfo.objects.update_or_create(
                external_id=external_id,
                shop=shop,
                defaults={
                    'product': product,
                    'model': model_name,
                    'price': price,
                    'price_rrc': price_rrc if price_rrc is not None else 0,  # Дефолтное значение
                    'quantity': quantity,
                }
            )
            action = "Создана" if created else "Обновлена"
            logger.debug(f"{action} информация о товаре (ID: {external_id}): {product_name} ({shop.name})")

            # Обработка параметров товара
            for param_name, param_value in parameters.items():
                if not param_name or not param_value:
                     logger.warning(f"Пропущен параметр с некорректными данными для товара {product_name}: ({param_name}, {param_value})")
                     continue

                parameter_obj, _ = Parameter.objects.get_or_create(name=param_name)
                ProductParameter.objects.update_or_create(
                    product_info=product_info,
                    parameter=parameter_obj,
                    defaults={'value': param_value}
                )
                logger.debug(f"  Параметр '{param_name}': {param_value} для товара {product_name}")

        return {'Status': True, 'Message': f'Импорт из {filepath_or_url} завершен успешно.'}

    except FileNotFoundError:
        logger.error(f"Файл {filepath_or_url} не найден.")
        return {'Status': False, 'Error': f'Файл {filepath_or_url} не найден.'}
    except yaml.YAMLError as e:
        logger.error(f"Ошибка парсинга YAML из {filepath_or_url}: {str(e)}")
        return {'Status': False, 'Error': f'Ошибка парсинга YAML: {str(e)}'}
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при импорте из {filepath_or_url}: {str(e)}")
        return {'Status': False, 'Error': f'Непредвиденная ошибка: {str(e)}'}
