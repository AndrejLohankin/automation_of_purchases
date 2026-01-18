# backend/admin.py

from django.contrib import admin
from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken

# --- Способ 1: Простая регистрация (закомментировано, т.к. используем декораторы) ---
# admin.site.register(Shop)
# admin.site.register(Category)
# admin.site.register(Product)
# admin.site.register(ProductInfo) # <-- Эта строка конфликтовала
# admin.site.register(Parameter)
# admin.site.register(ProductParameter)
# admin.site.register(Order)
# admin.site.register(OrderItem)
# admin.site.register(Contact)
# admin.site.register(ConfirmEmailToken)

# --- Способ 2: Регистрация с кастомизацией (используем этот) ---

# Пример кастомизации для ProductInfo
@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'external_id', 'model', 'price', 'quantity')
    list_filter = ('shop', 'product__category')
    search_fields = ('product__name', 'model', 'external_id')
    # Можно добавить raw_id_fields для связей с большим количеством записей
    # raw_id_fields = ("product", "shop") # Полезно, если много товаров/магазинов

# Регистрируем остальные модели с возможной кастомизацией
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'state')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('product_info', 'parameter', 'value')
    # raw_id_fields = ("product_info", "parameter") # Полезно при большом количестве

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'dt', 'state', 'contact')
    list_filter = ('state', 'dt', 'user')
    search_fields = ('user__email',) # Поиск по email пользователя

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_info', 'quantity')
    # raw_id_fields = ("order", "product_info") # Полезно при большом количестве

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'house', 'phone')
    search_fields = ('user__email', 'city', 'phone')

@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'key')

# User регистрировать не обязательно, если используется стандартная интеграция с AUTH_USER_MODEL
# Если хочешь кастомизировать, нужно будет создать UserAdmin и зарегистрировать явно.
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth import get_user_model
# User = get_user_model()
# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     # Здесь можно добавить или изменить поля для отображения
#     pass
