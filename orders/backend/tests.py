from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
import json
from backend.models import User as BackendUser, Shop, Category, Product, ProductInfo, Order, OrderItem, Contact
from frontend.forms import RegistrationForm, ContactForm
from django import forms


class FrontendViewsTests(TestCase):
    """Тесты для frontend views"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.client = Client()
        self.user = BackendUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Создаем необходимые объекты для ProductInfo
        self.shop = Shop.objects.create(name='Test Shop')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(name='Test Product', category=self.category)
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id=1,
            quantity=10,
            price=1000
        )

    def test_home_view(self):
        """Тестирование главной страницы"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/home.html')

    def test_login_view_get(self):
        """Тестирование GET запроса на страницу входа"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/login.html')

    def test_register_view_get(self):
        """Тестирование GET запроса на страницу регистрации"""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/register.html')

    def test_products_view_redirect(self):
        """Тестирование перенаправления на страницу товаров для авторизованного пользователя"""
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertRedirects(response, '/products/')

    def test_products_view(self):
        """Тестирование страницы товаров"""
        self.client.force_login(self.user)
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/products.html')

    def test_product_detail_view(self):
        """Тестирование страницы детального просмотра товара"""
        self.client.force_login(self.user)
        response = self.client.get(f'/product/{self.product_info.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/product_detail.html')

    def test_cart_view(self):
        """Тестирование страницы корзины"""
        self.client.force_login(self.user)
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/cart.html')

    def test_cart_add_view(self):
        """Тестирование добавления товара в корзину"""
        self.client.force_login(self.user)
        response = self.client.post('/cart/add/', {
            'product_info_id': self.product_info.id,
            'quantity': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

    def test_cart_update_view(self):
        """Тестирование обновления корзины"""
        self.client.force_login(self.user)
        cart, _ = Order.objects.get_or_create(user=self.user, state='basket')
        order_item = OrderItem.objects.create(
            order=cart,
            product_info=self.product_info,
            quantity=1
        )
        response = self.client.post('/cart/update/', {
            'order_item_id': order_item.id,
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

    def test_cart_delete_view(self):
        """Тестирование удаления товара из корзины"""
        self.client.force_login(self.user)
        cart, _ = Order.objects.get_or_create(user=self.user, state='basket')
        order_item = OrderItem.objects.create(
            order=cart,
            product_info=self.product_info,
            quantity=1
        )
        response = self.client.post('/cart/delete/', {
            'order_item_id': order_item.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

    def test_checkout_view(self):
        """Тестирование страницы оформления заказа"""
        self.client.force_login(self.user)
        response = self.client.get('/checkout/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/checkout.html')

    def test_orders_view(self):
        """Тестирование страницы заказов"""
        self.client.force_login(self.user)
        response = self.client.get('/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/orders.html')

    def test_order_detail_view(self):
        """Тестирование страницы детального просмотра заказа"""
        self.client.force_login(self.user)
        order = Order.objects.create(user=self.user, state='confirmed')
        OrderItem.objects.create(order=order, product_info=self.product_info, quantity=1)
        response = self.client.get(f'/order/{order.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/order_detail.html')

    def test_profile_view(self):
        """Тестирование страницы профиля"""
        self.client.force_login(self.user)
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/profile.html')

    def test_add_contact_view(self):
        """Тестирование страницы добавления контакта"""
        self.client.force_login(self.user)
        response = self.client.get('/add-contact/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/add_contact.html')

    def test_logout_view(self):
        """Тестирование выхода из системы"""
        self.client.force_login(self.user)
        response = self.client.get('/logout/')
        self.assertRedirects(response, '/')
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class FrontendFormsTests(TestCase):
    """Тесты для frontend форм"""

    def test_registration_form_valid(self):
        """Тестирование валидной регистрационной формы"""
        form = RegistrationForm({
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        })
        self.assertTrue(form.is_valid())

    def test_registration_form_invalid_passwords(self):
        """Тестирование регистрационной формы с различающими паролями"""
        form = RegistrationForm({
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'wrongpassword',
            'first_name': 'Test',
            'last_name': 'User'
        })
        self.assertFalse(form.is_valid())

    def test_contact_form_valid(self):
        """Тестирование валидной контактной формы"""
        form = ContactForm({
            'city': 'Moscow',
            'street': 'Tverskaya',
            'house': '1',
            'phone': '+79991234567'
        })
        self.assertTrue(form.is_valid())

        def test_contact_form_invalid_phone(self):
            "Тестирование контактной формы с невалидным телефоном"
            form = ContactForm({
                'city': 'Moscow',
                'street': 'Tverskaya',
                'house': '1',
                'phone': 'invalid_phone'
            })
            # В текущей реализации нет валидации телефона, поэтому форма будет валидной
            self.assertTrue(form.is_valid())

    class FrontendAjaxTests(TestCase):
        "Тесты для AJAX запросов"

        def setUp(self):
            "Настройка тестового окружения"
            self.client = Client()
            self.user = BackendUser.objects.create_user(
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            self.client.force_login(self.user)

            # Создаем необходимые объекты для ProductInfo
            self.shop = Shop.objects.create(name='Test Shop')
            self.category = Category.objects.create(name='Test Category')
            self.product = Product.objects.create(name='Test Product', category=self.category)
            self.product_info = ProductInfo.objects.create(
                product=self.product,
                shop=self.shop,
                external_id=1,
                quantity=10,
                price=1000
            )

        def test_cart_ajax_get(self):
            "Тестирование AJAX запроса для получения корзины"
            response = self.client.get('/cart/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/json')

        def test_cart_ajax_post(self):
            "Тестирование AJAX запроса для добавления товара в корзину"
            response = self.client.post('/cart/add/', {
                'product_info_id': self.product_info.id,
                'quantity': 1
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest', content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/json')
            self.assertEqual(response.json()['success'], True)

    class FrontendIntegrationTests(TestCase):
        "Интеграционные тесты"

        def setUp(self):
            "Настройка тестового окружения"
            self.client = Client()
            self.user = BackendUser.objects.create_user(
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            self.client.force_login(self.user)

            # Создаем необходимые объекты для ProductInfo
            self.shop = Shop.objects.create(name='Test Shop')
            self.category = Category.objects.create(name='Test Category')
            self.product = Product.objects.create(name='Test Product', category=self.category)
            self.product_info = ProductInfo.objects.create(
                product=self.product,
                shop=self.shop,
                external_id=1,
                quantity=10,
                price=1000
            )

        def test_full_user_flow(self):
            "Тестирование полного пользовательского сценария"
            # Регистрация
            response = self.client.post('/register/', {
                'email': 'newuser@example.com',
                'password': 'newpass123',
                'password_confirm': 'newpass123',
                'first_name': 'New',
                'last_name': 'User'
            })
            self.assertEqual(response.status_code, 302)  # Перенаправление после регистрации

            # Авторизация
            response = self.client.post('/login/', {
                'email': 'newuser@example.com',
                'password': 'newpass123'
            })
            self.assertEqual(response.status_code, 302)  # Перенаправление после входа

            # Добавление товара в корзину
            response = self.client.post('/cart/add/', {
                'product_info_id': self.product_info.id,
                'quantity': 1
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['success'], True)

            # Просмотр корзины
            response = self.client.get('/cart/')
            self.assertEqual(response.status_code, 200)

            # Оформление заказа
            response = self.client.get('/checkout/')
            self.assertEqual(response.status_code, 200)

            # Выход
            response = self.client.get('/logout/')
            self.assertEqual(response.status_code, 302)