# backend/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact, STATE_CHOICES


class UserLoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа пользователя.
    """
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                               email=email, password=password)

            if not user:
                raise serializers.ValidationError('Неверный email или пароль.')
        else:
            raise serializers.ValidationError('Email и пароль обязательны.')

        attrs['user'] = user
        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ('name',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = ParameterSerializer(read_only=True)
    # parameter_id = serializers.PrimaryKeyRelatedField(queryset=Parameter.objects.all(), write_only=True)

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('name',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('name',)


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'shop', 'model', 'price', 'quantity', 'product_parameters')


class CartItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)
    total_price = serializers.ReadOnlyField(source='get_total_price') # Предполагаем метод в модели

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'total_price')


class OrderItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)
    total_price = serializers.ReadOnlyField(source='get_total_price')

    class Meta:
        model = OrderItem
        fields = ('product_info', 'quantity', 'total_price')


class AddContactSerializer(serializers.ModelSerializer):
    contact_id = serializers.IntegerField(source='id', read_only=True) # <-- Добавляем новое поле

    class Meta:
        model = Contact
        fields = ('contact_id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone')

    def create(self, validated_data):
        # user заполняется автоматически во view
        return super().create(validated_data)


class OrderConfirmationSerializer(serializers.Serializer):
    basket_id = serializers.IntegerField()
    contact_id = serializers.IntegerField()

    def validate_basket_id(self, value):
        # Проверяем, что корзина принадлежит пользователю и имеет статус 'basket'
        request = self.context.get('request')
        try:
            order = Order.objects.get(id=value, user=request.user, state='basket')
        except Order.DoesNotExist:
            raise serializers.ValidationError("Корзина не найдена или не принадлежит вам.")
        return order

    def validate_contact_id(self, value):
        # Проверяем, что контакт принадлежит пользователю
        request = self.context.get('request')
        try:
            contact = Contact.objects.get(id=value, user=request.user)
        except Contact.DoesNotExist:
            raise serializers.ValidationError("Контакт не найден или не принадлежит вам.")
        return contact


class OrderHistorySerializer(serializers.ModelSerializer):
    ordered_items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()  # Добавляем информацию о контакте

    class Meta:
        model = Order
        fields = ('id', 'dt', 'state', 'ordered_items', 'total_price', 'contact_info')

    def get_total_price(self, obj):
        """Рассчитываем общую стоимость заказа."""
        total = sum(item.get_total_price() for item in obj.ordered_items.all())
        return total

    def get_contact_info(self, obj):
        """Возвращаем информацию о контакте."""
        if obj.contact:
            return {
                'city': obj.contact.city,
                'street': obj.contact.street,
                'house': obj.contact.house,
                'phone': obj.contact.phone
            }
        return None


class OrderStatusUpdateSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=STATE_CHOICES, required=True)

    def validate_state(self, value):
        """Проверяем, что статус является допустимым"""
        if value not in dict(STATE_CHOICES):
            raise serializers.ValidationError(f"Недопустимый статус: {value}")
        return value