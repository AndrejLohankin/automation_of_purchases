from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from .forms import RegistrationForm, ContactForm
from django.conf import settings
from backend.models import User
from django.db.models import Sum


@csrf_exempt
def home(request):
    """Главная страница"""
    if request.user.is_authenticated:
        return redirect('products')
    return render(request, 'frontend/home.html')


@csrf_exempt
def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Пробуем аутентифицироваться напрямую
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            return redirect('products')
        else:
            return render(request, 'frontend/login.html', {'error': 'Неверный email или пароль'})
    return render(request, 'frontend/login.html')


@csrf_exempt
def register_view(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid:
            # Создаем пользователя напрямую
            user = form.save()
            # Автоматически логинем пользователя после регистрации
            login(request, user)
            return redirect('products')
        else:
            return render(request, 'frontend/register.html', {'form': form, 'error': 'Ошибка регистрации'})
    else:
        form = RegistrationForm()
    return render(request, 'frontend/register.html', {'form': form})


@login_required
def products(request):
    """Список товаров"""
    page = request.GET.get('page', 1)
    category = request.GET.get('category')
    search = request.GET.get('search')

    # Получаем товары напрямую из базы данных
    from backend.models import ProductInfo, Category

    products = ProductInfo.objects.select_related('product', 'shop').prefetch_related('product_parameters__parameter')

    # Фильтруем по категории
    if category and category != 'None':
        products = products.filter(product__category_id=category)

    # Ищем по названию
    if search and search != 'None':
        products = products.filter(product__name__icontains=search)

    # Пагинация
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12)  # 12 товаров на страницу
    products_page = paginator.get_page(page)

    # Получаем категории для фильтра
    categories = Category.objects.all()

    return render(request, 'frontend/products.html', {
        'products': products_page,
        'page': page,
        'category': category,
        'search': search,
        'categories': categories
    })


@login_required
def product_detail(request, product_id):
    """Детальная страница товара"""
    from backend.models import ProductInfo

    product = get_object_or_404(ProductInfo, id=product_id)

    # Получаем связанные товары из той же категории
    related_products = ProductInfo.objects.filter(
        product__category=product.product.category
    ).exclude(id=product.id)[:4]  # Первые 4 товара

    return render(request, 'frontend/product_detail.html', {
        'product': product,
        'related_products': related_products
    })


@login_required
def cart(request):
    """Корзина"""
    from backend.models import Order, OrderItem

    # Получаем корзину
    cart, created = Order.objects.get_or_create(
        user=request.user,
        state='basket'
    )

    # Получаем элементы корзины
    items = cart.ordered_items.select_related('product_info__product').all()

    # Вычисляем общую стоимость
    total_price = 0
    for item in items:
        item.total_price = item.product_info.price * item.quantity
        total_price += item.total_price

    return render(request, 'frontend/cart.html', {
        'cart': {
            'items': items,
            'total_price': total_price
        }
    })


@login_required
def add_to_cart(request):
    """Добавить товар в корзину"""
    if request.method == 'POST':
        product_info_id = request.POST.get('product_info_id')
        quantity = request.POST.get('quantity', 1)

        # Получаем товар из базы данных
        from backend.models import ProductInfo, Order, OrderItem
        from django.db.models import Sum  # Правильный импорт

        try:
            product_info = ProductInfo.objects.get(id=product_info_id)
        except ProductInfo.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Товар не найден'})

        # Получаем или создаем корзину
        cart, created = Order.objects.get_or_create(
            user=request.user,
            state='basket'
        )

        # Проверяем доступное количество
        if int(quantity) > product_info.quantity:
            return JsonResponse({'success': False, 'message': 'Недостаточно товара на складе'})

        # Создаем или обновляем позицию в корзине
        order_item, created = OrderItem.objects.get_or_create(
            order=cart,
            product_info=product_info,
            defaults={'quantity': quantity}
        )

        if not created:
            # Обновляем количество, если товар уже в корзине
            order_item.quantity += int(quantity)
            if order_item.quantity > product_info.quantity:
                return JsonResponse({'success': False, 'message': 'Недостаточно товара на складе'})
            order_item.save()

        # Получаем общее количество товаров в корзине
        cart_count = cart.ordered_items.aggregate(Sum('quantity'))['quantity__sum'] or 0

        return JsonResponse({
            'success': True,
            'message': 'Товар добавлен в корзину',
            'cart_count': cart_count
        })


@login_required
def update_cart(request):
    """Обновить корзину"""
    if request.method == 'POST':
        order_item_id = request.POST.get('order_item_id')
        quantity = request.POST.get('quantity')

        from backend.models import OrderItem, ProductInfo
        from django.db.models import Sum  # Правильный импорт

        try:
            order_item = OrderItem.objects.select_related('product_info').get(id=order_item_id)
            product_info = order_item.product_info

            # Проверяем доступное количество
            if int(quantity) > product_info.quantity:
                return JsonResponse({'success': False, 'message': 'Недостаточно товара на складе'})

            if int(quantity) <= 0:
                order_item.delete()
                return JsonResponse({'success': True, 'message': 'Товар удален из корзины'})

            order_item.quantity = int(quantity)
            order_item.save()

            return JsonResponse({'success': True, 'message': 'Количество товара обновлено'})
        except OrderItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Товар не найден'})


@login_required
def delete_from_cart(request):
    """Удалить товар из корзины"""
    if request.method == 'POST':
        order_item_id = request.POST.get('order_item_id')

        from backend.models import OrderItem

        try:
            order_item = OrderItem.objects.get(id=order_item_id)
            order_item.delete()

            return JsonResponse({'success': True, 'message': 'Товар удален из корзины'})
        except OrderItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Товар не найден'})


@login_required
def cart_clear(request):
    """Очистить всю корзину"""
    from backend.models import Order, OrderItem
    from django.db.models import Sum  # Правильный импорт

    cart = Order.objects.filter(user=request.user, state='basket')
    deleted_count = OrderItem.objects.filter(order__in=cart).delete()[0]

    return JsonResponse({
        'success': True,
        'message': f'Корзина очищена. Удалено {deleted_count} товаров'
    })


@login_required
def checkout(request):
    """Оформление заказа"""
    if request.method == 'POST':
        basket_id = request.POST.get('basket_id')
        contact_id = request.POST.get('contact_id')

        # Обрабатываем заказ напрямую
        from backend.models import Order

        try:
            # Получаем корзину
            cart = Order.objects.get(id=basket_id, user=request.user, state='basket')

            # Обновляем статус заказа
            cart.state = 'confirmed'  # или 'new', как у вас принято
            cart.contact_id = contact_id
            cart.save()

            return redirect('orders')
        except Order.DoesNotExist:
            return render(request, 'frontend/checkout.html', {'error': 'Корзина не найдена'})

    # Получаем корзину
    from backend.models import Order, OrderItem

    cart, created = Order.objects.get_or_create(
        user=request.user,
        state='basket'
    )

    # Получаем элементы корзины
    items = cart.ordered_items.select_related('product_info__product').all()

    # Вычисляем общую стоимость
    total_price = 0
    for item in items:
        item.total_price = item.product_info.price * item.quantity
        total_price += item.total_price

    # Получаем контакты
    contacts = request.user.contacts.all()

    return render(request, 'frontend/checkout.html', {
        'cart': {
            'items': items,
            'total_price': total_price
        },
        'contacts': contacts
    })


@login_required
def orders(request):
    """Список заказов"""
    # Получаем историю заказов напрямую из базы данных
    from backend.models import Order

    # Получаем все заказы пользователя, кроме корзины
    orders = Order.objects.filter(user=request.user).exclude(state='basket').order_by('-dt')

    # Сериализуем данные для отображения
    orders_data = []
    for order in orders:
        items = order.ordered_items.select_related('product_info__product').all()
        order_items = []
        for item in items:
            item_data = {
                'id': item.id,
                'quantity': item.quantity,
                'product_info': {
                    'id': item.product_info.id,
                    'price': item.product_info.price,
                    'product': {
                        'name': item.product_info.product.name
                    }
                },
                'total_price': item.quantity * item.product_info.price
            }
            order_items.append(item_data)

        order_data = {
            'id': order.id,
            'dt': order.dt,
            'state': order.state,
            'items': order_items,
            'total_price': sum(item['total_price'] for item in order_items)
        }
        orders_data.append(order_data)

    return render(request, 'frontend/orders.html', {'orders': orders_data})


@login_required
def order_detail(request, order_id):
    """Детальная страница заказа"""
    # Получаем заказ напрямую из базы данных
    from backend.models import Order, OrderItem

    try:
        order = Order.objects.select_related('user').prefetch_related(
            'ordered_items__product_info__product'
        ).get(id=order_id, user=request.user)

        items = order.ordered_items.select_related('product_info__product').all()
        order_items = []
        for item in items:
            item_data = {
                'id': item.id,
                'quantity': item.quantity,
                'product_info': {
                    'id': item.product_info.id,
                    'price': item.product_info.price,
                    'product': {
                        'name': item.product_info.product.name
                    }
                },
                'total_price': item.quantity * item.product_info.price
            }
            order_items.append(item_data)

        order_data = {
            'id': order.id,
            'dt': order.dt,
            'state': order.state,
            'items': order_items,
            'total_price': sum(item['total_price'] for item in order_items)
        }

        return render(request, 'frontend/order_detail.html', {'order': order_data})
    except Order.DoesNotExist:
        return render(request, 'frontend/order_detail.html', {'error': 'Заказ не найден'})


@login_required
def profile(request):
    """Профиль пользователя"""
    return render(request, 'frontend/profile.html')


@login_required
def logout_view(request):
    """Выход пользователя"""
    logout(request)
    return redirect('home')


@login_required
def add_contact(request):
    """Добавить новый контакт"""
    if request.method == 'POST':
        city = request.POST.get('city')
        street = request.POST.get('street')
        house = request.POST.get('house')
        structure = request.POST.get('structure')
        building = request.POST.get('building')
        apartment = request.POST.get('apartment')
        phone = request.POST.get('phone')

        # Создаем новый контакт
        from backend.models import Contact

        contact = Contact.objects.create(
            user=request.user,
            city=city,
            street=street,
            house=house,
            structure=structure,
            building=building,
            apartment=apartment,
            phone=phone
        )

        # Возвращаемся на страницу оформления заказа
        return redirect('checkout')

    return render(request, 'frontend/add_contact.html')