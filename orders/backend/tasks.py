# backend/tasks.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order, User, ConfirmEmailToken # Импортируем ConfirmEmailToken

def send_registration_confirmation_email(user_email, user_id=None):
    """
    Отправляет письмо для подтверждения регистрации.
    Генерирует и сохраняет токен подтверждения.
    """
    # 1. Создаём токен для пользователя
    token_instance = ConfirmEmailToken.objects.create(user_id=user_id) # передаём user_id
    token_key = token_instance.key

    # 2. Формируем тему и сообщение
    subject = 'Подтверждение регистрации на сайте'
    # В реальном приложении здесь будет HTML-шаблон
    message_body_text = f"""
    Здравствуйте,

    Спасибо за регистрацию на нашем сайте.
    Пожалуйста, перейдите по следующей ссылке, чтобы подтвердить ваш email:

    http://yourdomain.com/confirm-email/{token_key}/


    Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.

    С уважением,
    Администрация сайта.
    """

    # 3. Отправляем письмо
    try:
        send_mail(
            subject,
            message_body_text,
            settings.DEFAULT_FROM_EMAIL, # Или конкретный адрес отправителя
            [user_email],
            fail_silently=False,
        )
        print(f"[EMAIL TASK] Confirmation email sent to {user_email} with token {token_key[:8]}...") # Логируем
        return True
    except Exception as e:
        print(f"[EMAIL TASK] FAILED to send confirmation email to {user_email}: {e}") # Логируем ошибку
        return False

def send_order_confirmation_email(order_id, contact_id):
    """
    Отправляет письмо с подтверждением заказа.
    """
    try:
        order = Order.objects.get(id=order_id)
        # contact = Contact.objects.get(id=contact_id) # Контакт уже привязан к заказу
        user_email = order.user.email

        subject = f'Подтверждение заказа #{order.id}'
        message_body_text = f"""
        Здравствуйте,

        Ваш заказ #{order.id} успешно подтвержден и находится в обработке.
        Статус: {order.get_state_display()}.
        Детали заказа можно посмотреть в личном кабинете.

        С уважением,
        Служба поддержки.
        """
        send_mail(
            subject,
            message_body_text,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"[EMAIL TASK] Order confirmation email sent for order {order_id} to {user_email}")
    except Order.DoesNotExist:
        print(f"[EMAIL TASK] Order {order_id} not found for confirmation email.")
    except Exception as e:
        print(f"[EMAIL TASK] Failed to send confirmation email for order {order_id}: {e}")
