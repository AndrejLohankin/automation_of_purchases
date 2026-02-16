from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, ConfirmEmailToken
import yaml
from .models import ImportTask, Shop, Category, Product, ProductInfo, Parameter, ProductParameter

@shared_task
def send_registration_confirmation_email(user_email, user_id=None):
    """Отправляет письмо для подтверждения регистрации"""
    try:
        token_instance = ConfirmEmailToken.objects.create(user_id=user_id)
        subject = 'Подтверждение регистрации на сайте'
        message = f"""
        Здравствуйте,

        Ваш токен подтверждения: {token_instance.key}

        С уважением, Администрация сайта.
        """
        send_mail(
            subject,
            message,
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
    """Отправляет письмо с подтверждением заказа"""
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Подтверждение заказа #{order.id}'
        message = f"""
        Ваш заказ #{order.id} подтвержден.
        Статус: {order.get_state_display()}.
        """
        send_mail(
            subject,
            message,
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
        shop_name = data.get('shop', 'Default')
        shop, _ = Shop.objects.get_or_create(name=shop_name)

        for cat_data in data.get('categories', []):
            Category.objects.get_or_create(id=cat_data['id'], defaults={'name': cat_data['name']})
            stats['categories'] += 1

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