# backend/admin.py

from django.contrib import admin
from .models import (
    User, Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken
)


# --- Inline для OrderItem ---
# Позволяет редактировать OrderItem прямо на странице Order
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Не показывать пустые строки для добавления
    # Если в модели OrderItem есть метод get_total_price, можно сделать его доступным только для чтения
    # readonly_fields = ('get_total_price',)
    can_delete = True  # Позволить удалять OrderItem через inline форму


# --- ModelAdmin Classes ---

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Показываем основные и кастомные поля
    list_display = ('email', 'first_name', 'last_name', 'type', 'company', 'position', 'is_active', 'date_joined')
    # Добавляем фильтры
    list_filter = ('type', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'company')
    # Поля для поиска
    search_fields = ('email', 'first_name', 'last_name', 'company', 'position')
    # Поля, которые можно редактировать
    # exclude = ('password',) # Пароль лучше не редактировать напрямую в админке
    # readonly_fields = ('email',) # Если хочешь запретить редактирование email после создания

    # Опционально: группировка полей на странице редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}), # Основная информация
        ('Personal info', {'fields': ('first_name', 'last_name', 'type', 'company', 'position')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'user', 'state')
    list_filter = ('state', 'user')
    search_fields = ('name', 'user__email')
    # raw_id_fields = ('user',) # Удобно, если много пользователей


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'external_id', 'model', 'price', 'quantity')
    list_filter = ('shop', 'product__category')
    search_fields = ('product__name', 'model', 'external_id', 'shop__name')
    # raw_id_fields = ("product", "shop") # Удобно, если много товаров/магазинов


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('product_info', 'parameter', 'value')
    list_filter = ('parameter', 'product_info__shop')
    search_fields = ('value', 'parameter__name', 'product_info__product__name')
    # raw_id_fields = ("product_info", "parameter") # Удобно, если много связей


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'contact')
    list_filter = ('state', 'dt', 'user')
    search_fields = ('user__email', 'id', 'contact__city', 'contact__phone')
    # raw_id_fields = ("user", "contact") # Удобно, если много пользователей/контактов
    inlines = [OrderItemInline]  # Подключаем inline для OrderItem

    # Опционально: добавить метод для отображения общей стоимости заказа
    # def total_cost(self, obj):
    #     # Предполагаем, что в модели Order есть метод get_total_cost()
    #     return obj.get_total_cost()
    # total_cost.short_description = 'Total Cost'


# @admin.register(OrderItem) # Закомментировано, так как OrderItem теперь управляется через OrderAdmin
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product_info', 'quantity', 'get_total_price') # Используем метод из модели
#     list_filter = ('order__state', 'product_info__shop') # Пример фильтрации
#     # raw_id_fields = ("order", "product_info") # Удобно, если много связей


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'house', 'phone')
    list_filter = ('city', 'user')
    search_fields = ('user__email', 'city', 'phone', 'street')


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'key')
    # Запрещаем редактирование токена и времени создания
    readonly_fields = ('key', 'created_at', 'user', 'created_at')
