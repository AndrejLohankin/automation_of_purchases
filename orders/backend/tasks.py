# backend/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, User, ConfirmEmailToken, ImportTask
import yaml
import logging
import requests
from urllib.parse import urlparse
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


@shared_task
def send_registration_confirmation_email(user_email, user_id=None):
    """
    Отправляет письмо для подтверждения регистрации.
    """
    token_instance = ConfirmEmailToken.objects.create(user_id=user_id)
    token_key = token_instance.key

    subject = 'Подтверждение регистрации на сайте'
    message_body_text = f"""
    Здравствуйте,

    Ваш токен подтверждения: {token_key}

    С уважением, Администрация сайта.
    """

    try:
        send_mail(
            subject,
            message_body_text,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"[CELERY] Email sent to {user_email}")
        return True
    except Exception as e:
        print(f"[CELERY] Email failed: {e}")
        return False


@shared_task
def send_order_confirmation_email(order_id, contact_id):
    """
    Отправляет письмо с подтверждением заказа.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Подтверждение заказа #{order.id}'
        message_body_text = f"""
        Ваш заказ #{order.id} подтвержден.
        Статус: {order.get_state_display()}.
        """
        send_mail(
            subject,
            message_body_text,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
        print(f"[CELERY] Order email sent for order {order_id}")
        return True
    except Order.DoesNotExist:
        print(f"[CELERY] Order {order_id} not found")
        return False
    except Exception as e:
        print(f"[CELERY] Order email failed: {e}")
        return False


@shared_task
def do_import(import_task_id):
    """Асинхронный импорт товаров из YAML"""
    from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

    try:
        import_task = ImportTask.objects.get(id=import_task_id)
        data = yaml.safe_load(import_task.yaml_file.read().decode('utf-8'))

        stats = {'products': 0, 'categories': 0, 'parameters': 0}
        shop_name = data.get('shop', 'Default Shop')
        shop, _ = Shop.objects.get_or_create(name=shop_name)

        # Импорт категорий
        for cat_data in data.get('categories', []):
            Category.objects.get_or_create(id=cat_data['id'], defaults={'name': cat_data['name']})
            stats['categories'] += 1

        # Импорт товаров
        for good in data.get('goods', []):
            category = Category.objects.get(id=good['category'])
            product, _ = Product.objects.get_or_create(name=good['name'], defaults={'category': category})

            ProductInfo.objects.update_or_create(
                external_id=good['id'],
                shop=shop,
                defaults={
                    'product': product,
                    'quantity': good.get('quantity', 0),
                    'price': good.get('price', 0),
                }
            )
            stats['products'] += 1

            for param_name, param_value in good.get('parameters', {}).items():
                parameter, _ = Parameter.objects.get_or_create(name=param_name)
                ProductParameter.objects.update_or_create(
                    product_info=ProductInfo.objects.get(external_id=good['id'], shop=shop),
                    parameter=parameter,
                    defaults={'value': str(param_value)}
                )
                stats['parameters'] += 1

        import_task.is_processed = True
        import_task.products_count = stats['products']
        import_task.categories_count = stats['categories']
        import_task.parameters_count = stats['parameters']
        import_task.save()

        print(f"[CELERY] Import completed: {stats}")
        return stats

    except Exception as e:
        print(f"[CELERY] Import failed: {e}")
        return False

# ============ Асинхронная обработка изображений ============

@shared_task(bind=True, max_retries=3)
def process_product_image(self, product_id, image_url=None):
    """
    Асинхронная задача для обработки изображения товара.
    Создает миниатюры различных размеров.

    Args:
        product_id: ID продукта
        image_url: URL изображения (опционально)
    """
    from backend.models import Product
    from easy_thumbnails.files import generate_all_aliases

    try:
        product = Product.objects.get(id=product_id)

        if image_url:
            # Скачиваем изображение по URL
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                # Получаем имя файла из URL
                parsed_url = urlparse(image_url)
                filename = parsed_url.path.split('/')[-1]
                if not filename:
                    filename = f'product_{product_id}.jpg'

                # Сохраняем изображение
                image_content = ContentFile(response.content)
                product.image.save(filename, image_content, save=True)
                logger.info(f"Downloaded image for product {product_id}: {filename}")
            else:
                logger.warning(f"Failed to download image for product {product_id}: HTTP {response.status_code}")
                return {'status': 'error', 'message': f'HTTP {response.status_code}'}

        # Генерируем миниатюры
        if product.image:
            generate_all_aliases(product.image, include_global=False)
            logger.info(f"Generated thumbnails for product {product_id}")
            return {'status': 'success', 'product_id': product_id}
        else:
            return {'status': 'warning', 'message': 'No image to process'}

    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
        return {'status': 'error', 'message': 'Product not found'}
    except Exception as exc:
        logger.exception(f"Error processing image for product {product_id}")
        self.retry(exc=exc, countdown=60)


@shared_task
def batch_process_images(product_ids):
    """
    Пакетная обработка изображений для нескольких товаров.

    Args:
        product_ids: Список ID товаров
    """
    results = []
    for product_id in product_ids:
        result = process_product_image.delay(product_id)
        results.append({'product_id': product_id, 'task_id': result.id})

    return {
        'status': 'queued',
        'total': len(product_ids),
        'tasks': results
    }


@shared_task
def cleanup_old_images(days=30):
    """
    Удаление старых неиспользуемых изображений.
    Запускается периодически (например, раз в неделю).
    """
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    # Находим товары с изображениями
    old_products = Product.objects.filter(
        image__isnull=False,
        updated_at__lt=cutoff_date
    )

    deleted_count = 0
    for product in old_products:
        if product.image:
            product.image.delete(save=True)
            deleted_count += 1

    logger.info(f"Cleaned up {deleted_count} old product images")
    return {'deleted_count': deleted_count}
