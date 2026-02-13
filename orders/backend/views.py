# backend/views.py

from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact
from .serializers import (
    UserLoginSerializer, UserRegistrationSerializer, ProductInfoSerializer,
    CartItemSerializer, AddContactSerializer, OrderConfirmationSerializer,
    OrderHistorySerializer
)
from rest_framework.authtoken.models import Token  # Если используем TokenAuthentication


class LoginView(APIView):
    """
    Вход пользователя.
    """

    def post(self, request):
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
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # --- НОВЫЙ КОД ---
            # Вызываем функцию отправки email подтверждения
            from .tasks import send_registration_confirmation_email
            success = send_registration_confirmation_email(user.email, user.id)
            if success:
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

    def post(self, request):
        serializer = OrderConfirmationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            basket = serializer.validated_data['basket_id']
            contact = serializer.validated_data['contact_id']

            # Обновляем статус корзины
            basket.state = 'confirmed' # или 'new', как у тебя принято
            basket.contact = contact
            basket.save()

            # --- НОВЫЙ КОД ---
            # Запускаем задачу на отправку email
            from .tasks import send_order_confirmation_email
            send_order_confirmation_email(basket.id, contact.id)
            # ----------------

            return Response({'message': 'Заказ подтвержден. Информация продублирована на Вашу почту.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderHistoryView(generics.ListAPIView):
    """
    История заказов пользователя.
    """
    serializer_class = OrderHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем все заказы пользователя, кроме корзины
        return Order.objects.filter(user=self.request.user).exclude(state='basket').order_by('-dt')

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