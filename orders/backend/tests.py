
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Order
from rest_framework import status


class OrderStatusUpdateTests(TestCase):
    """Тесты для обновления статуса заказа"""

    def setUp(self):
        # Создаем администратора
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )

        # Создаем обычного пользователя
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            first_name='Test',
            last_name='User'
        )

        # Создаем заказ
        self.order = Order.objects.create(
            user=self.regular_user,
            state='new'
        )

        self.client = Client()

    def test_admin_can_update_order_status(self):
        """Тест: администратор может обновить статус заказа"""
        # Аутентификация администратора
        self.client.login(email='admin@example.com', password='adminpass123')

        # Данные для обновления
        update_data = {
            'state': 'confirmed'
        }

        # Отправляем запрос
        response = self.client.put(f'/api/v1/orders/{self.order.id}/status/',
                                   update_data,
                                   content_type='application/json')

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['new_state'], 'confirmed')
        self.assertEqual(response.json()['new_state_display'], 'Подтвержден')

    def test_regular_user_cannot_update_order_status(self):
        """Тест: обычный пользователь не может обновить статус заказа"""
        # Аутентификация обычного пользователя
        self.client.login(email='user@example.com', password='userpass123')

        # Данные для обновления
        update_data = {
            'state': 'confirmed'
        }

        # Отправляем запрос
        response = self.client.put(f'/api/v1/orders/{self.order.id}/status/',
                                   update_data,
                                   content_type='application/json')

        # Проверяем ответ (должен быть 403 - запрещено)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_order_status(self):
        """Тест: нельзя установить несуществующий статус"""
        # Аутентификация администратора
        self.client.login(email='admin@example.com', password='adminpass123')

        # Данные с несуществующим статусом
        update_data = {
            'state': 'invalid_status'
        }

        # Отправляем запрос
        response = self.client.put(f'/api/v1/orders/{self.order.id}/status/',
                                   update_data,
                                   content_type='application/json')

        # Проверяем ответ (должен быть 400 - ошибка валидации)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Недопустимый статус', response.json()['state'][0])

    def test_nonexistent_order(self):
        """Тест: нельзя обновить несуществующий заказ"""
        # Аутентификация администратора
        self.client.login(email='admin@example.com', password='adminpass123')

        # Данные для обновления
        update_data = {
            'state': 'confirmed'
        }

        # Пытаемся обновить несуществующий заказ
        response = self.client.put('/api/v1/orders/99999/status/',
                                   update_data,
                                   content_type='application/json')

        # Проверяем ответ (должен быть 404 - не найден)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_order_status_with_get_method(self):
        """Тест: метод GET не должен работать для обновления статуса"""
        # Аутентификация администратора
        self.client.login(email='admin@example.com', password='adminpass123')

        # Отправляем GET запрос
        response = self.client.get(f'/api/v1/orders/{self.order.id}/status/')

        # Проверяем ответ (должен быть 405 - метод не разрешен)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class OrderStatusUpdateIntegrationTests(TestCase):
    """Интеграционные тесты для обновления статуса заказа"""

    def setUp(self):
        # Создаем администратора
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )

        # Создаем несколько заказов
        self.order1 = Order.objects.create(user=self.admin_user, state='new')
        self.order2 = Order.objects.create(user=self.admin_user, state='confirmed')
        self.order3 = Order.objects.create(user=self.admin_user, state='assembled')

        self.client = Client()

    def test_bulk_order_status_update(self):
        """Тест: администратор может обновить статусы нескольких заказов"""
        # Аутентификация администратора
        self.client.login(email='admin@example.com', password='adminpass123')

        # Обновляем статусы нескольких заказов
        response1 = self.client.put(f'/api/v1/orders/{self.order1.id}/status/',
                                    {'state': 'sent'},
                                    content_type='application/json')

        response2 = self.client.put(f'/api/v1/orders/{self.order2.id}/status/',
                                    {'state': 'sent'},
                                    content_type='application/json')

        response3 = self.client.put(f'/api/v1/orders/{self.order3.id}/status/',
                                    {'state': 'sent'},
                                    content_type='application/json')

        # Проверяем все ответы
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        # Проверяем, что статусы действительно обновлены
        self.order1.refresh_from_db()
        self.order2.refresh_from_db()
        self.order3.refresh_from_db()

        self.assertEqual(self.order1.state, 'sent')
        self.assertEqual(self.order2.state, 'sent')
        self.assertEqual(self.order3.state, 'sent')

    def test_order_status_transition_logic(self):
        """Тест: проверка логики переходов между статусами"""
        # Аутентификация администратора
        self.client.login(email='admin@example.com', password='adminpass123')

        # Проверяем возможные переходы
        test_cases = [
            ('new', 'confirmed'),
            ('confirmed', 'assembled'),
            ('assembled', 'sent'),
            ('sent', 'delivered'),
            ('new', 'canceled'),
            ('confirmed', 'canceled'),
        ]

        for current_state, new_state in test_cases:
            # Создаем заказ с текущим статусом
            order = Order.objects.create(user=self.admin_user, state=current_state)

            # Обновляем статус
            response = self.client.put(f'/api/v1/orders/{order.id}/status/',
                                       {'state': new_state},
                                       content_type='application/json')

            # Проверяем ответ
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Проверяем, что статус действительно обновлен
            order.refresh_from_db()
            self.assertEqual(order.state, new_state)

            # Удаляем заказ
            order.delete()

# --- КОНЕЦ ТЕСТОВ ДЛЯ РЕДАКТИРОВАНИЯ СТАТУСА ЗАКАЗА ---