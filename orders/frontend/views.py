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

API_BASE_URL = f'http://{settings.ALLOWED_HOSTS[0]}/api/v1/' if settings.ALLOWED_HOSTS else 'http://localhost:8000/api/v1/'

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

        # Пробуем через API
        response = requests.post(f'{API_BASE_URL}login/', data={'email': email, 'password': password})

        if response.status_code == 200:
            # Создаем или получаем пользователя Django
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'is_active': True}
            )

            # Вручную аутентифицируем пользователя
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
        if form.is_valid():
            response = requests.post(f'{API_BASE_URL}register/', data=form.cleaned_data)
            
            if response.status_code == 201:
                return redirect('login')
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
    
    params = {'page': page}
    if category:
        params['category_id'] = category
    if search:
        params['search'] = search
    
    response = requests.get(f'{API_BASE_URL}products/', params=params)
    
    if response.status_code == 200:
        products = response.json()
        return render(request, 'frontend/products.html', {'products': products, 'page': page, 'category': category, 'search': search})
    else:
        return render(request, 'frontend/products.html', {'error': 'Ошибка загрузки товаров'})

@login_required
def product_detail(request, product_id):
    """Детальная страница товара"""
    response = requests.get(f'{API_BASE_URL}products/{product_id}/')
    
    if response.status_code == 200:
        product = response.json()
        return render(request, 'frontend/product_detail.html', {'product': product})
    else:
        return render(request, 'frontend/product_detail.html', {'error': 'Товар не найден'})

@login_required
def cart(request):
    """Корзина"""
    response = requests.get(f'{API_BASE_URL}basket/')
    
    if response.status_code == 200:
        cart_data = response.json()
        return render(request, 'frontend/cart.html', {'cart': cart_data})
    else:
        return render(request, 'frontend/cart.html', {'error': 'Ошибка загрузки корзины'})

@login_required
def add_to_cart(request):
    """Добавить товар в корзину"""
    if request.method == 'POST':
        product_info_id = request.POST.get('product_info_id')
        quantity = request.POST.get('quantity', 1)
        
        response = requests.post(f'{API_BASE_URL}basket/', data={'product_info_id': product_info_id, 'quantity': quantity})
        
        if response.status_code == 201:
            return JsonResponse({'success': True, 'message': 'Товар добавлен в корзину'})
        else:
            return JsonResponse({'success': False, 'message': 'Ошибка добавления товара'})

@login_required
def update_cart(request):
    """Обновить корзину"""
    if request.method == 'POST':
        order_item_id = request.POST.get('order_item_id')
        quantity = request.POST.get('quantity')
        
        response = requests.put(f'{API_BASE_URL}basket/', data={'order_item_id': order_item_id, 'quantity': quantity})
        
        if response.status_code == 200:
            return JsonResponse({'success': True, 'message': 'Корзина обновлена'})
        else:
            return JsonResponse({'success': False, 'message': 'Ошибка обновления корзины'})

@login_required
def delete_from_cart(request):
    """Удалить товар из корзины"""
    if request.method == 'POST':
        order_item_id = request.POST.get('order_item_id')
        
        response = requests.delete(f'{API_BASE_URL}cart/delete/?order_item_id={order_item_id}')
        
        if response.status_code == 200:
            return JsonResponse({'success': True, 'message': 'Товар удален из корзины'})
        else:
            return JsonResponse({'success': False, 'message': 'Ошибка удаления товара'})

@login_required
def checkout(request):
    """Оформление заказа"""
    if request.method == 'POST':
        basket_id = request.POST.get('basket_id')
        contact_id = request.POST.get('contact_id')
        
        response = requests.post(f'{API_BASE_URL}orders/confirm/', data={'basket_id': basket_id, 'contact_id': contact_id})
        
        if response.status_code == 200:
            return redirect('orders')
        else:
            return render(request, 'frontend/checkout.html', {'error': 'Ошибка оформления заказа'})
    
    # Получаем корзину
    cart_response = requests.get(f'{API_BASE_URL}basket/')
    if cart_response.status_code == 200:
        cart_data = cart_response.json()
    else:
        cart_data = {'items': []}
    
    # Получаем контакты
    contacts_response = requests.get(f'{API_BASE_URL}contacts/list/')
    if contacts_response.status_code == 200:
        contacts = contacts_response.json()
    else:
        contacts = []
    
    return render(request, 'frontend/checkout.html', {'cart': cart_data, 'contacts': contacts})

@login_required
def orders(request):
    """Список заказов"""
    response = requests.get(f'{API_BASE_URL}orders/history/')
    
    if response.status_code == 200:
        orders = response.json()
        return render(request, 'frontend/orders.html', {'orders': orders})
    else:
        return render(request, 'frontend/orders.html', {'error': 'Ошибка загрузки заказов'})

@login_required
def order_detail(request, order_id):
    """Детальная страница заказа"""
    response = requests.get(f'{API_BASE_URL}orders/{order_id}/')
    
    if response.status_code == 200:
        order = response.json()
        return render(request, 'frontend/order_detail.html', {'order': order})
    else:
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