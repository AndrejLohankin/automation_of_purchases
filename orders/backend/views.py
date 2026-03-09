# backend/views.py

from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from rest_framework import generics, status

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact
from .serializers import (
    UserLoginSerializer, UserRegistrationSerializer, ProductInfoSerializer,
    CartItemSerializer, AddContactSerializer, OrderConfirmationSerializer,
    OrderHistorySerializer, OrderStatusUpdateSerializer, AddToCartSerializer,
    UpdateCartItemSerializer, DeleteCartItemSerializer, BatchDeleteCartItemsSerializer,
    DeleteContactSerializer
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from .tasks import do_import
from .models import ImportTask
import yaml
from datetime import datetime
from django.http import StreamingHttpResponse
import io

class LoginView(APIView):
    """
    Вход пользователя.
    """
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        login(request, user)  # Устанавливаем сессию (работает с SessionAuthentication)

        # Если используешь TokenAuthentication:
        # token, created = Token.objects.get_or_create(user=user)
        # return Response({'token': token.key})

        # Если просто сессия, возвращаем успех
        return Response({'message': 'Успешный вход'}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    Регистрация пользователя.
    """
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # --- НОВЫЙ КОД ---
            # Запускаем задачу на отправку email подтверждения через Celery
            from .tasks import send_registration_confirmation_email
            task = send_registration_confirmation_email.delay(user.email, user.id)
            if task:
                message = 'Пользователь успешно зарегистрирован. Проверьте ваш email для подтверждения.'
            else:
                message = 'Пользователь успешно зарегистрирован, но письмо подтверждения не было отправлено.'
            # ----------------
            return Response({'message': message}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductListView(generics.ListAPIView):
    """
    Список товаров.
    """
    queryset = ProductInfo.objects.select_related('product', 'shop').prefetch_related('product_parameters__parameter')
    serializer_class = ProductInfoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Пример фильтрации по shop_id и category_id
        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')
        # Пример поиска по названию продукта
        search = self.request.query_params.get('search')

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        if search:
            queryset = queryset.filter(product__name__icontains=search)

        return queryset


class CartView(APIView):
    """
    Управление корзиной.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AddToCartSerializer

    def get_serializer_class(self):
        """Возвращаем разные сериализаторы для разных методов"""
        if self.request.method == 'POST':
            return AddToCartSerializer
        elif self.request.method == 'PUT':
            return UpdateCartItemSerializer
        return AddToCartSerializer

    def get(self, request):
        """
        Получить содержимое корзины и её ID.
        """
        # Получаем или создаём корзину (Order со статусом 'basket') для текущего пользователя
        cart, created = Order.objects.get_or_create(user=request.user, state='basket')

        # Получаем элементы корзины (OrderItem)
        items = cart.ordered_items.all()

        # Сериализуем элементы
        serializer = CartItemSerializer(items, many=True)

        # Возвращаем ID корзины и содержимое
        return Response({
            'basket_id': cart.id,  # <-- Добавляем ID корзины
            'items': serializer.data
        })

    def post(self, request):
        """
        Добавить товар в корзину.
        """
        cart, created = Order.objects.get_or_create(user=request.user, state='basket')
        product_info_id = request.data.get('product_info_id')
        quantity = request.data.get('quantity', 1)

        if not product_info_id or not quantity:
            return Response({'error': 'product_info_id и quantity обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        product_info = get_object_or_404(ProductInfo, id=product_info_id)

        # Проверяем доступное количество
        if quantity > product_info.quantity:
            return Response({'error': 'Недостаточно товара на складе'}, status=status.HTTP_400_BAD_REQUEST)

        order_item, created = OrderItem.objects.get_or_create(
            order=cart,
            product_info=product_info,
            defaults={'quantity': quantity}
        )
        if not created:
            # Обновляем количество, если товар уже в корзине
            order_item.quantity += int(quantity)
            # Проверяем снова после увеличения
            if order_item.quantity > product_info.quantity:
                return Response({'error': 'Недостаточно товара на складе'}, status=status.HTTP_400_BAD_REQUEST)
            order_item.save()

        return Response({'message': 'Товар добавлен в корзину'}, status=status.HTTP_201_CREATED)

    def put(self, request):
        """
        Обновить количество товара в корзине.
        """
        cart = get_object_or_404(Order, user=request.user, state='basket')
        order_item_id = request.data.get('order_item_id')
        quantity = request.data.get('quantity')

        if not order_item_id or quantity is None:
            return Response({'error': 'order_item_id и quantity обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        order_item = get_object_or_404(OrderItem, id=order_item_id, order=cart)
        product_info = order_item.product_info

        # Проверяем доступное количество
        if int(quantity) > product_info.quantity:
            return Response({'error': 'Недостаточно товара на складе'}, status=status.HTTP_400_BAD_REQUEST)

        if int(quantity) <= 0:
            order_item.delete()
            return Response({'message': 'Товар удален из корзины'}, status=status.HTTP_200_OK)

        order_item.quantity = int(quantity)
        order_item.save()
        return Response({'message': 'Количество товара обновлено'}, status=status.HTTP_200_OK)

    def delete(self, request):
        """
        Удалить товар из корзины.
        """
        cart = get_object_or_404(Order, user=request.user, state='basket')
        order_item_id = request.query_params.get('order_item_id')

        if not order_item_id:
            return Response({'error': 'order_item_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        order_item = get_object_or_404(OrderItem, id=order_item_id, order=cart)
        order_item.delete()
        return Response({'message': 'Товар удален из корзины'}, status=status.HTTP_204_NO_CONTENT)


class AddContactView(generics.CreateAPIView):
    """
    Добавить контакт.
    """
    serializer_class = AddContactSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Привязываем контакт к текущему пользователю
        user = self.request.user
        serializer.save(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Возвращаем только ID созданного контакта
        headers = self.get_success_headers(serializer.data)
        return Response({'contact_id': serializer.instance.id}, status=status.HTTP_201_CREATED, headers=headers)


class OrderConfirmationView(APIView):
    """
    Подтвердить заказ.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderConfirmationSerializer

    def post(self, request):
        serializer = OrderConfirmationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            basket = serializer.validated_data['basket_id']
            contact = serializer.validated_data['contact_id']

            # Обновляем статус корзины
            basket.state = 'confirmed'  # или 'new', как у тебя принято
            basket.contact = contact
            basket.save()

            # Запускаем задачу на отправку email через Celery
            from .tasks import send_order_confirmation_email
            task = send_order_confirmation_email.delay(basket.id, contact.id)
            # ----------------

            return Response({'message': 'Заказ подтвержден. Информация продублирована на Вашу почту.'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderHistoryView(generics.ListAPIView):
    """История заказов пользователя."""
    serializer_class = OrderHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращаем все заказы пользователя, кроме корзины.

        Оптимизация: используем prefetch_related для избежания N+1 запросов.
        Загружаем ordered_items с связанными product_info, product, shop и контактами.
        """
        return Order.objects.filter(user=self.request.user).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'contact'
        ).order_by('-dt')

    def get(self, request):
        """Получить историю заказов с фильтрацией."""
        orders = self.get_queryset()

        # Фильтрация по статусу
        status = request.query_params.get('status')
        if status:
            orders = orders.filter(state=status)

        # Фильтрация по периоду
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            orders = orders.filter(dt__gte=start_date)
        if end_date:
            orders = orders.filter(dt__lte=end_date)

        serializer = OrderHistorySerializer(orders, many=True)
        return Response({
            'orders': serializer.data,
            'total': orders.count()
        })

class ContactListView(generics.ListAPIView):
    """
    Получить список контактов пользователя.
    Только аутентифицированный пользователь может получить свои контакты.
    """
    # Можно создать отдельный сериализатор, если нужно больше контроля
    # или исключить поля из представления. Пока используем AddContactSerializer.
    serializer_class = AddContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только контакты текущего аутентифицированного пользователя
        user = self.request.user
        return Contact.objects.filter(user=user)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def trigger_import(request):
    """Запуск задачи импорта из админки через Celery"""
    import_task_id = request.data.get('import_task_id')
    if not import_task_id:
        return Response({'error': 'import_task_id required'}, status=400)

    try:
        import_task = ImportTask.objects.get(id=import_task_id)
        if import_task.is_processed:
            return Response({'error': 'Import already processed'}, status=400)

        # Запускаем задачу Celery
        task = do_import.delay(import_task_id)

        return Response({
            'task_id': task.id,
            'status': 'started',
            'import_task_id': import_task_id
        })
    except ImportTask.DoesNotExist:
        return Response({'error': 'ImportTask not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# --- НОВЫЙ КОД ---

class DeleteCartItemView(APIView):
    """
    Удалить товар из корзины по ID.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteCartItemSerializer

    def delete(self, request):
        """
        Удалить товар из корзины.
        """
        cart = get_object_or_404(Order, user=request.user, state='basket')
        order_item_id = request.query_params.get('order_item_id')

        if not order_item_id:
            return Response({'error': 'order_item_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        order_item = get_object_or_404(OrderItem, id=order_item_id, order=cart)
        order_item.delete()
        return Response({'message': 'Товар удален из корзины'}, status=status.HTTP_200_OK)


class DetailedContactListView(generics.ListAPIView):
    """
    Получить детальную информацию о контактах пользователя.
    """
    serializer_class = AddContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только контакты текущего аутентифицированного пользователя
        user = self.request.user
        return Contact.objects.filter(user=user)

    def get(self, request):
        """
        Получить детальный список контактов с возможностью фильтрации.
        """
        contacts = self.get_queryset()

        # Фильтрация по городу
        city = request.query_params.get('city')
        if city:
            contacts = contacts.filter(city__icontains=city)

        # Фильтрация по телефону
        phone = request.query_params.get('phone')
        if phone:
            contacts = contacts.filter(phone__icontains=phone)

        serializer = AddContactSerializer(contacts, many=True)
        return Response({
            'contacts': serializer.data,
            'total': contacts.count()
        })


class ContactDetailView(generics.RetrieveAPIView):
    """
    Получить детальную информацию о конкретном контакте.
    """
    serializer_class = AddContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только контакты текущего аутентифицированного пользователя
        user = self.request.user
        return Contact.objects.filter(user=user)

    def get_object(self):
        contact_id = self.kwargs.get('contact_id')
        return get_object_or_404(self.get_queryset(), id=contact_id)


class BatchDeleteCartItemView(APIView):
    """
    Удалить несколько товаров из корзины одновременно.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BatchDeleteCartItemsSerializer

    def post(self, request):
        """
        Удалить несколько товаров из корзины.

        Пример запроса:
        {
            "order_item_ids": [3, 5, 7]
        }
        """
        cart = get_object_or_404(Order, user=request.user, state='basket')
        order_item_ids = request.data.get('order_item_ids')

        if not order_item_ids or not isinstance(order_item_ids, list):
            return Response({'error': 'order_item_ids должен быть списком ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Удаляем все указанные товары
        deleted_count = OrderItem.objects.filter(
            order=cart,
            id__in=order_item_ids
        ).delete()[0]

        return Response({
            'message': f'Удалено {deleted_count} товаров из корзины',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)


class ClearCartView(APIView):
    """
    Очистить всю корзину.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """
        Удалить все товары из корзины.
        """
        cart = get_object_or_404(Order, user=request.user, state='basket')

        # Удаляем все товары из корзины
        deleted_count = cart.ordered_items.all().delete()[0]

        return Response({
            'message': f'Корзина очищена. Удалено {deleted_count} товаров',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)

class DeleteContactView(APIView):
    """Удалить контакт по ID."""
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteContactSerializer

    def delete(self, request):
        """Удалить контакт."""
        contact_id = request.query_params.get('contact_id')
        if not contact_id:
            return Response({'error': 'contact_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        contact = get_object_or_404(Contact, id=contact_id, user=request.user)
        contact.delete()
        return Response({'message': 'Контакт удален'}, status=status.HTTP_200_OK)

class OrderDetailView(generics.RetrieveAPIView):
    """Получить детальную информацию о конкретном заказе."""
    serializer_class = OrderHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращаем только заказы текущего пользователя."""
        return Order.objects.filter(user=self.request.user).exclude(state='basket')

    def get_object(self):
        order_id = self.kwargs.get('order_id')
        return get_object_or_404(self.get_queryset(), id=order_id)

class ProductSpecificationView(generics.RetrieveAPIView):
    """Получить спецификацию по отдельному товару."""
    serializer_class = ProductInfoSerializer
    permission_classes = [AllowAny]  # Для неавторизованных пользователей

    def get_queryset(self):
        """Возвращаем все товары."""
        return ProductInfo.objects.select_related('product', 'shop').prefetch_related('product_parameters__parameter')

    def get_object(self):
        product_info_id = self.kwargs.get('product_info_id')
        return get_object_or_404(self.get_queryset(), id=product_info_id)


# --- НОВЫЙ КОД ДЛЯ РЕДАКТИРОВАНИЯ СТАТУСА ЗАКАЗА ---

class OrderStatusUpdateView(APIView):
    """
    Обновление статуса заказа (только для администраторов).
    """
    permission_classes = [IsAdminUser]
    serializer_class = OrderStatusUpdateSerializer

    def put(self, request, order_id):
        """
        Обновить статус заказа.
        """
        order = get_object_or_404(Order, id=order_id)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_state = serializer.validated_data['state']

        # Обновляем статус заказа
        order.state = new_state
        order.save()

        return Response({
            'message': f'Статус заказа обновлен на: {order.get_state_display()}',
            'order_id': order.id,
            'new_state': new_state,
            'new_state_display': order.get_state_display()
        }, status=status.HTTP_200_OK)


class ProductExportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Получаем все товары с информацией
            products = ProductInfo.objects.select_related('product', 'shop').prefetch_related(
                'product_parameters__parameter'
            )

            # Создаем структуру данных для экспорта
            export_data = []

            # Группируем товары по магазинам
            shops = products.values('shop__name').distinct()

            for shop in shops:
                shop_name = shop['shop__name'] if shop['shop__name'] else 'Default Shop'

                # Получаем товары для текущего магазина
                shop_products = products.filter(shop__name=shop_name)

                # Создаем структуру для текущего магазина
                shop_data = {
                    'shop': shop_name,
                    'categories': [],
                    'goods': []
                }

                # Собираем уникальные категории
                categories_set = set()
                for product_info in shop_products:
                    if product_info.product.category:
                        categories_set.add(product_info.product.category)

                # Добавляем категории
                for category in categories_set:
                    shop_data['categories'].append({
                        'id': category.id,
                        'name': category.name
                    })

                # Добавляем товары
                for product_info in shop_products:
                    # Собираем параметры товара
                    parameters = {}
                    for param in product_info.product_parameters.all():
                        parameters[param.parameter.name] = param.value

                    shop_data['goods'].append({
                        'id': product_info.external_id,
                        'name': product_info.product.name,
                        'category': product_info.product.category.id if product_info.product.category else None,
                        'quantity': product_info.quantity,
                        'price': product_info.price,
                        'parameters': parameters
                    })

                # Добавляем структуру магазина в общий экспорт
                export_data.append(shop_data)

            # Конвертируем в YAML с правильными отступами
            yaml_data = yaml.dump(export_data, sort_keys=False, indent=2)

            # Создаем поток для файла
            stream = io.StringIO()
            stream.write(yaml_data)
            stream.seek(0)

            # Возвращаем как файл
            response = StreamingHttpResponse(
                stream,
                content_type='application/x-yaml; charset=utf-8'
            )
            response[
                'Content-Disposition'] = f'attachment; filename="export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml"'

            return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def export_products(request):
    try:
        shop_id = request.data.get('shop_id')
        category_id = request.data.get('category_id')

        # Фильтруем товары
        queryset = ProductInfo.objects.select_related('product', 'shop').prefetch_related(
            'product_parameters__parameter'
        )

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)

        # Создаем структуру данных для экспорта
        export_data = []

        # Группируем товары по магазинам
        shops = queryset.values('shop__name').distinct()

        for shop in shops:
            shop_name = shop['shop__name'] if shop['shop__name'] else 'Default Shop'

            # Получаем товары для текущего магазина
            shop_products = queryset.filter(shop__name=shop_name)

            # Создаем структуру для текущего магазина
            shop_data = {
                'shop': shop_name,
                'categories': [],
                'goods': []
            }

            # Собираем уникальные категории
            categories_set = set()
            for product_info in shop_products:
                if product_info.product.category:
                    categories_set.add(product_info.product.category)

            # Добавляем категории
            for category in categories_set:
                shop_data['categories'].append({
                    'id': category.id,
                    'name': category.name
                })

            # Добавляем товары
            for product_info in shop_products:
                # Собираем параметры товара
                parameters = {}
                for param in product_info.product_parameters.all():
                    parameters[param.parameter.name] = param.value

                shop_data['goods'].append({
                    'id': product_info.external_id,
                    'name': product_info.product.name,
                    'category': product_info.product.category.id if product_info.product.category else None,
                    'quantity': product_info.quantity,
                    'price': product_info.price,
                    'parameters': parameters
                })

            # Добавляем структуру магазина в общий экспорт
            export_data.append(shop_data)

        # Конвертируем в YAML
        yaml_data = yaml.dump(export_data, sort_keys=False)

        # Создаем поток для файла
        stream = io.StringIO()
        stream.write(yaml_data)
        stream.seek(0)

        # Возвращаем как файл
        response = StreamingHttpResponse(
            stream,
            content_type='application/x-yaml; charset=utf-8'
        )
        response[
            'Content-Disposition'] = f'attachment; filename="filtered_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml"'

        return response

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Социальная авторизация ---

class GoogleAuthView(APIView):
    """
    Начало аутентификации через Google.
    Перенаправляет пользователя на страницу Google.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from django.urls import reverse
        # Формируем URL для редиректа на Google OAuth
        redirect_url = reverse('social:begin', kwargs={'backend': 'google-oauth2'})
        return Response({
            'auth_url': request.build_absolute_uri(redirect_url)
        })


class TelegramAuthView(APIView):
    """
    Начало аутентификации через Telegram.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from django.urls import reverse
        redirect_url = reverse('social:begin', kwargs={'backend': 'telegram'})
        return Response({
            'auth_url': request.build_absolute_uri(redirect_url)
        })

# --- Асинхронная обработка изображений ---

class ProductImageUploadView(APIView):
    """
    Загрузка изображения товара.
    Изображение обрабатывается асинхронно через Celery.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Загрузить изображение для товара.

        Способы загрузки:
        1. По URL (асинхронно):
           {"product_id": 1, "image_url": "https://example.com/image.jpg"}

        2. Из файла (multipart/form-data):
           - product_id: 1
           - image: <файл>

        3. Base64 в JSON (синхронно):
           {"product_id": 1, "image_base64": "<base64 строка>", "filename": "image.jpg"}
        """
        product_id = request.data.get('product_id')
        image_url = request.data.get('image_url')
        image_file = request.FILES.get('image')
        image_base64 = request.data.get('image_base64')
        filename = request.data.get('filename', 'image.jpg')

        if not product_id:
            return Response({'error': 'product_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Если передан URL изображения
        if image_url:
            from .tasks import process_product_image
            task = process_product_image.delay(product_id, image_url)
            return Response({
                'message': 'Изображение будет загружено асинхронно',
                'task_id': task.id,
                'product_id': product_id
            }, status=status.HTTP_202_ACCEPTED)

        # Если передан файл изображения
        elif image_file:
            product.image = image_file
            product.save()

            from easy_thumbnails.files import generate_all_aliases
            generate_all_aliases(product.image, include_global=False)

            return Response({
                'message': 'Изображение успешно загружено',
                'product_id': product_id,
                'image_url': request.build_absolute_uri(product.image.url)
            }, status=status.HTTP_201_CREATED)

        # Если передано base64 изображение
        elif image_base64:
            import base64
            try:
                # Декодируем base64
                image_data = base64.b64decode(image_base64)
                # Определяем расширение по имени файла
                ext = filename.split('.')[-1] if '.' in filename else 'jpg'
                if ext.lower() not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    ext = 'jpg'
                final_filename = f"{product_id}_{int(datetime.now().timestamp())}.{ext}"

                # Сохраняем файл
                from django.core.files.base import ContentFile
                product.image.save(final_filename, ContentFile(image_data), save=True)

                # Генерируем миниатюры
                from easy_thumbnails.files import generate_all_aliases
                generate_all_aliases(product.image, include_global=False)

                return Response({
                    'message': 'Изображение успешно загружено',
                    'product_id': product_id,
                    'image_url': request.build_absolute_uri(product.image.url)
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': f'Ошибка при обработке изображения: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Необходимо передать image_url, image (файл) или image_base64'}, status=status.HTTP_400_BAD_REQUEST)


class ProductImageBatchUploadView(APIView):
    """
    Пакетная загрузка изображений для нескольких товаров.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Загрузить изображения для нескольких товаров.

        Пример запроса:
        POST /api/products/batch-upload/
        {
            "products": [
                {"product_id": 1, "image_url": "https://example.com/1.jpg"},
                {"product_id": 2, "image_url": "https://example.com/2.jpg"},
                {"product_id": 3}
            ]
        }
        """
        products = request.data.get('products', [])

        if not products:
            return Response({'error': 'products обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        from .tasks import batch_process_images
        product_ids = [p['product_id'] for p in products if 'product_id' in p]

        if not product_ids:
            return Response({'error': 'Необходимо указать product_id'}, status=status.HTTP_400_BAD_REQUEST)

        # Запускаем пакетную обработку
        result = batch_process_images.delay(product_ids)

        return Response({
            'message': 'Задача на пакетную загрузку изображений запущена',
            'task_id': result.id,
            'total_products': len(product_ids)
        }, status=status.HTTP_202_ACCEPTED)


# --- Sentry Test ---
class SentryTestView(APIView):
    """
    Тестовый view для проверки работы Sentry.
    При вызове намеренно вызывает исключение для проверки мониторинга.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Тестовый endpoint для проверки Sentry.
        """
        # Проверяем, есть ли DSN
        from django.conf import settings
        if not getattr(settings, 'SENTRY_DSN', None):
            return Response({
                'message': 'Sentry не настроен. Установите SENTRY_DSN в переменных окружения.',
                'sentry_status': 'disabled'
            })

        # Намеренно вызываем исключение для проверки
        try:
            raise ValueError("Тестовая ошибка Sentry! Это сообщение должно появиться в Sentry.")
        except ValueError as e:
            # Логируем исключение в Sentry
            import sentry_sdk
            sentry_sdk.capture_exception(e)
            return Response({
                'message': 'Тестовая ошибка отправлена в Sentry',
                'sentry_status': 'enabled',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- CacheOps Performance Test ---
class CachePerformanceTestView(APIView):
    """
    Тестовый view для измерения производительности кэширования.
    Показывает количество запросов к БД и время выполнения.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        import time
        from django.db import connection, reset_queries
        from django.conf import settings

        # Включаем отладку запросов
        old_debug = settings.DEBUG
        settings.DEBUG = True
        reset_queries()

        # Замеряем время выполнения
        start_time = time.time()

        # Выполняем тестовый запрос к БД (список товаров)
        products = ProductInfo.objects.select_related('product', 'shop').prefetch_related(
            'product_parameters__parameter'
        )[:10]

        # Сериализуем данные
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'name': p.product.name,
                'shop': p.shop.name if p.shop else None,
                'price': str(p.price),
            })

        execution_time = time.time() - start_time
        query_count = len(connection.queries)

        settings.DEBUG = old_debug

        # Информация о кэше
        from django.core.cache import cache
        cache_stats = {
            'cache_backend': str(type(cache)).split('.')[-1].replace("'>", ""),
            'cache_enabled': True,
        }

        return Response({
            'message': 'Тест производительности кэширования',
            'results': {
                'products_count': len(data),
                'query_count': query_count,
                'execution_time_ms': round(execution_time * 1000, 2),
                'cache': cache_stats,
            },
            'note': 'При повторном запросе количество запросов к БД должно быть 0 (данные из кэша)'
        })


# --- Django Silk: N+1 Query Detection ---
class OrderHistoryPerformanceTestView(APIView):
    """
    Тестовый view для демонстрации проблемы N+1 запросов в OrderHistoryView.
    Показывает количество запросов к БД при получении истории заказов.

    Проблема: в OrderHistorySerializer.get_total_price используется obj.ordered_items.all()
    Решение: добавить prefetch_related('ordered_items__product_info')
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import time
        from django.db import connection, reset_queries
        from django.conf import settings
        from .models import Order

        # Включаем отладку запросов
        old_debug = settings.DEBUG
        settings.DEBUG = True
        reset_queries()

        # Замеряем время выполнения
        start_time = time.time()

        # === ВАРИАНТ 1: БЕЗ OPTIMIZATION (проблема N+1) ===
        # Это аналог текущего OrderHistoryView
        orders_without_optimization = Order.objects.filter(
            user=request.user
        ).exclude(state='basket').order_by('-dt')

        # Сериализуем - здесь происходит N+1 запросов!
        from .serializers import OrderHistorySerializer
        serializer_bad = OrderHistorySerializer(orders_without_optimization, many=True)
        data_bad = serializer_bad.data

        query_count_bad = len(connection.queries)
        time_bad = time.time() - start_time

        # Сбрасываем счётчик запросов
        reset_queries()
        start_time = time.time()

        # === ВАРИАНТ 2: С OPTIMIZATION (решение N+1) ===
        # Добавляем prefetch_related для оптимизации
        orders_with_optimization = Order.objects.filter(
            user=request.user
        ).exclude(state='basket').order_by('-dt').prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'contact'
        )

        serializer_good = OrderHistorySerializer(orders_with_optimization, many=True)
        data_good = serializer_good.data

        query_count_good = len(connection.queries)
        time_good = time.time() - start_time

        settings.DEBUG = old_debug

        return Response({
            'message': 'Тест производительности OrderHistoryView (N+1 detection)',
            'without_optimization': {
                'query_count': query_count_bad,
                'execution_time_ms': round(time_bad * 1000, 2),
                'orders_count': len(data_bad),
                'note': 'Каждый заказ делает отдельный запрос для ordered_items и contact (проблема N+1)'
            },
            'with_optimization': {
                'query_count': query_count_good,
                'execution_time_ms': round(time_good * 1000, 2),
                'orders_count': len(data_good),
                'note': 'Используется prefetch_related - все данные загружаются за 2-3 запроса'
            },
            'improvement': {
                'query_reduction': f'{query_count_bad - query_count_good} запросов',
                'time_improvement_ms': round((time_bad - time_good) * 1000, 2),
                'recommendation': 'Добавить .prefetch_related("ordered_items__product_info__product", "ordered_items__product_info__shop", "contact") в OrderHistoryView.get_queryset()'
            }
        })
