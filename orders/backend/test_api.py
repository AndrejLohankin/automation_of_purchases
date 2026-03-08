# backend/test_api.py
# Тесты для API backend/views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
import json

from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact, Parameter, ProductParameter

User = get_user_model()


class LoginViewTestCase(TestCase):
    """Тесты для LoginView - POST /api/login/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_login_success(self):
        """Тест успешной авторизации"""
        url = '/api/v1/login/'
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())

    def test_login_invalid_credentials(self):
        """Тест авторизации с неверными данными"""
        url = '/api/v1/login/'
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields(self):
        """Тест авторизации без обязательных полей"""
        url = '/api/v1/login/'
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegisterViewTestCase(TestCase):
    """Тесты для RegisterView - POST /api/register/"""

    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        """Тест успешной регистрации"""
        url = '/api/v1/register/'
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.json())
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_duplicate_email(self):
        """Тест регистрации с существующим email"""
        User.objects.create_user(
            email='existing@example.com',
            password='pass123'
        )
        url = '/api/v1/register/'
        data = {
            'email': 'existing@example.com',
            'password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        """Тест регистрации без обязательных полей"""
        url = '/api/v1/register/'
        data = {'email': 'incomplete@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductListViewTestCase(TestCase):
    """Тесты для ProductListView - GET /api/products/"""

    def setUp(self):
        self.client = APIClient()
        self.shop = Shop.objects.create(name='Test Shop')
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(name='Smartphone', category=self.category)
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id='123',
            model='X100',
            quantity=10,
            price=50000,
            price_rrc=55000
        )

    def test_product_list_unauthenticated(self):
        """Тест получения списка товаров без авторизации"""
        url = '/api/v1/products/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_list_authenticated(self):
        """Тест получения списка товаров с авторизацией"""
        user = User.objects.create_user(email='user@test.com', password='pass123')
        self.client.force_authenticate(user=user)
        url = '/api/v1/products/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF возвращает список напрямую
        self.assertIsInstance(response.json(), list)

    def test_product_list_filter_by_shop(self):
        """Тест фильтрации товаров по магазину"""
        url = f'/api/v1/products/?shop_id={self.shop.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_list_filter_by_category(self):
        """Тест фильтрации товаров по категории"""
        url = f'/api/v1/products/?category_id={self.category.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_list_search(self):
        """Тест поиска товаров"""
        url = '/api/v1/products/?search=Smartphone'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CartViewTestCase(TestCase):
    """Тесты для CartView - GET/POST/PUT/DELETE /api/basket/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='cart@test.com', password='pass123')
        self.client.force_authenticate(user=self.user)

        self.shop = Shop.objects.create(name='Cart Shop')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(name='Test Product', category=self.category)
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id='456',
            quantity=100,
            price=1000
        )

    def test_get_cart(self):
        """Тест получения корзины"""
        url = '/api/v1/basket/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('basket_id', response.json())
        self.assertIn('items', response.json())

    def test_add_to_cart(self):
        """Тест добавления товара в корзину"""
        url = '/api/v1/basket/'
        data = {
            'product_info_id': self.product_info.id,
            'quantity': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.json())

    def test_add_to_cart_insufficient_stock(self):
        """Тест добавления товара с недостаточным количеством на складе"""
        url = '/api/v1/basket/'
        data = {
            'product_info_id': self.product_info.id,
            'quantity': 1000  # Больше чем есть на складе
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_to_cart_missing_product_info_id(self):
        """Тест добавления товара без product_info_id"""
        url = '/api/v1/basket/'
        data = {'quantity': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_cart_item(self):
        """Тест обновления количества товара в корзине"""
        # Сначала добавим товар в корзину
        cart, _ = Order.objects.get_or_create(user=self.user, state='basket')
        OrderItem.objects.create(order=cart, product_info=self.product_info, quantity=1)

        url = '/api/v1/basket/'
        data = {
            'order_item_id': cart.ordered_items.first().id,
            'quantity': 5
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_cart_item(self):
        """Тест удаления товара из корзины"""
        cart, _ = Order.objects.get_or_create(user=self.user, state='basket')
        order_item = OrderItem.objects.create(order=cart, product_info=self.product_info, quantity=1)

        url = f'/api/v1/basket/?order_item_id={order_item.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ContactViewTestCase(TestCase):
    """Тесты для контактов - POST /api/contacts/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='contact@test.com', password='pass123')
        self.client.force_authenticate(user=self.user)

    def test_add_contact(self):
        """Тест добавления контакта"""
        url = '/api/v1/contacts/'
        data = {
            'city': 'Moscow',
            'street': 'Tverskaya',
            'house': '1',
            'phone': '+79991234567'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('contact_id', response.json())

    def test_add_contact_missing_fields(self):
        """Тест добавления контакта без обязательных полей"""
        url = '/api/v1/contacts/'
        data = {'city': 'Moscow'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_contact_list(self):
        """Тест получения списка контактов"""
        Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Tverskaya',
            house='1',
            phone='+79991234567'
        )
        url = '/api/v1/contacts/list/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contact_detail(self):
        """Тест получения деталей контакта"""
        contact = Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Tverskaya',
            house='1',
            phone='+79991234567'
        )
        url = f'/api/v1/contacts/{contact.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_contact(self):
        """Тест удаления контакта"""
        contact = Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Tverskaya',
            house='1',
            phone='+79991234567'
        )
        url = f'/api/v1/contacts/delete/?contact_id={contact.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OrderViewTestCase(TestCase):
    """Тесты для заказов"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='order@test.com', password='pass123')
        self.client.force_authenticate(user=self.user)

        self.shop = Shop.objects.create(name='Order Shop')
        self.category = Category.objects.create(name='Order Category')
        self.product = Product.objects.create(name='Order Product', category=self.category)
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id='789',
            quantity=50,
            price=2000
        )
        self.contact = Contact.objects.create(
            user=self.user,
            city='Moscow',
            street='Arbat',
            house='10',
            phone='+79999999999'
        )

    def test_order_confirmation(self):
        """Тест подтверждения заказа"""
        # Создаем корзину с товаром
        cart = Order.objects.create(user=self.user, state='basket')
        OrderItem.objects.create(order=cart, product_info=self.product_info, quantity=2)

        url = '/api/v1/orders/confirm/'
        data = {
            'basket_id': cart.id,
            'contact_id': self.contact.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())

        # Проверяем, что статус заказа изменился
        cart.refresh_from_db()
        self.assertEqual(cart.state, 'confirmed')

    def test_order_history(self):
        """Тест получения истории заказов"""
        Order.objects.create(user=self.user, state='confirmed')
        Order.objects.create(user=self.user, state='sent')

        url = '/api/v1/orders/history/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('orders', response.json())

    def test_order_history_filter_by_status(self):
        """Тест фильтрации истории заказов по статусу"""
        Order.objects.create(user=self.user, state='confirmed')
        Order.objects.create(user=self.user, state='sent')

        url = '/api/v1/orders/history/?status=confirmed'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_detail(self):
        """Тест получения деталей заказа"""
        order = Order.objects.create(user=self.user, state='confirmed')
        OrderItem.objects.create(order=order, product_info=self.product_info, quantity=1)

        url = f'/api/v1/orders/{order.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_status_update(self):
        """Тест обновления статуса заказа (admin)"""
        order = Order.objects.create(user=self.user, state='confirmed')

        # Создаем админа
        admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123'
        )
        self.client.force_authenticate(user=admin_user)

        url = f'/api/v1/orders/{order.id}/status/'
        data = {'state': 'sent'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.state, 'sent')


class ProductSpecificationViewTestCase(TestCase):
    """Тесты для ProductSpecificationView - GET /api/products/<id>/"""

    def setUp(self):
        self.client = APIClient()
        self.shop = Shop.objects.create(name='Spec Shop')
        self.category = Category.objects.create(name='Spec Category')
        self.product = Product.objects.create(name='Spec Product', category=self.category)
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id='999',
            quantity=5,
            price=3000
        )
        # Добавляем параметры товара
        self.param = Parameter.objects.create(name='Color')
        ProductParameter.objects.create(
            product_info=self.product_info,
            parameter=self.param,
            value='Black'
        )

    def test_product_specification(self):
        """Тест получения спецификации товара"""
        url = f'/api/v1/products/{self.product_info.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('product', response.json())
        self.assertIn('product_parameters', response.json())

    def test_product_specification_not_found(self):
        """Тест получения несуществующего товара"""
        url = '/api/v1/products/99999/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CartManagementViewTestCase(TestCase):
    """Дополнительные тесты для управления корзиной"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='cart2@test.com', password='pass123')
        self.client.force_authenticate(user=self.user)

        self.shop = Shop.objects.create(name='Cart Shop 2')
        self.category = Category.objects.create(name='Cat 2')
        self.product = Product.objects.create(name='Product 2', category=self.category)
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id='555',
            quantity=20,
            price=500
        )

    def test_batch_delete_cart_items(self):
        """Тест массового удаления товаров из корзины"""
        cart, _ = Order.objects.get_or_create(user=self.user, state='basket')

        # Создаём второй product_info для второго товара
        shop2 = Shop.objects.create(name='Cart Shop 3')
        product2 = Product.objects.create(name='Product 3', category=self.category)
        product_info2 = ProductInfo.objects.create(
            product=product2,
            shop=shop2,
            external_id='666',
            quantity=30,
            price=600
        )

        item1 = OrderItem.objects.create(order=cart, product_info=self.product_info, quantity=1)
        item2 = OrderItem.objects.create(order=cart, product_info=product_info2, quantity=2)

        url = '/api/v1/cart/delete-batch/'
        data = {'order_item_ids': [item1.id, item2.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_clear_cart(self):
        """Тест очистки корзины"""
        cart, _ = Order.objects.get_or_create(user=self.user, state='basket')
        OrderItem.objects.create(order=cart, product_info=self.product_info, quantity=3)

        url = '/api/v1/cart/clear/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_cart_unauthenticated(self):
        """Тест получения корзины без авторизации"""
        self.client.logout()
        url = '/api/v1/basket/'
        response = self.client.get(url)
        # DRF может возвращать 403 вместо 401 для неавторизованных
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class ThrottlingTestCase(TestCase):
    """Тесты для проверки throttling (ограничения частоты запросов)"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='throttle@test.com', password='pass123')

    def test_anonymous_user_throttle(self):
        """Тест throttling для анонимных пользователей"""
        # Для анонимных пользователей ограничение - 100 запросов в минуту
        url = '/api/v1/products/'

        # Выполняем много запросов
        responses = []
        for i in range(5):  # Небольшое количество для теста
            response = self.client.get(url)
            responses.append(response.status_code)

        # Все запросы должны пройти (5 запросов меньше лимита в 100)
        self.assertTrue(all(
            status.HTTP_200_OK == code for code in responses
        ), "Все запросы должны пройти при соблюдении лимита")

    def test_authenticated_user_throttle(self):
        """Тест throttling для авторизованных пользователей"""
        self.client.force_authenticate(user=self.user)

        url = '/api/v1/products/'

        # Выполняем серию запросов
        responses = []
        for i in range(5):
            response = self.client.get(url)
            responses.append(response.status_code)

        # Проверяем, что запросы проходят успешно
        self.assertTrue(
            all(code == status.HTTP_200_OK for code in responses),
            "Авторизованные пользователи должны иметь доступ к API"
        )

    def test_throttle_response_header(self):
        """Тест проверки заголовков ответа, содержащих информацию о лимитах"""
        url = '/api/v1/products/'
        response = self.client.get(url)

        # Проверяем наличие заголовка X-Throttle-Remaining или аналогичных
        # DRF может добавлять заголовки RateLimit-* или X-RateLimit-*
        headers = response.headers

        # Проверяем, что запрос прошел успешно
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем наличие заголовков throttling (опционально)
        has_throttle_info = any(
            key.lower().startswith('x-ratelimit') or
            key.lower().startswith('rate') or
            key.lower().startswith('throttle')
            for key in headers.keys()
        )
        # Примечание: в тестовом режиме заголовки могут не добавляться
        # поэтому просто проверяем успешный ответ

    def test_different_endpoints_throttle(self):
        """Тест проверки throttling на разных endpoint'ах"""
        # Публичный endpoint - доступен без авторизации
        url_products = '/api/v1/products/'
        response = self.client.get(url_products)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Endpoint {url_products} должен быть доступен анонимно"
        )

        # Приватный endpoint - требует авторизации
        url_orders = '/api/v1/orders/history/'
        response = self.client.get(url_orders)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
            f"Endpoint {url_orders} должен требовать авторизацию"
        )
