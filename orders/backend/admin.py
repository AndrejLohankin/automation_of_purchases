from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.html import format_html
import yaml
from django.core.files.storage import default_storage
from .models import (
    User, Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken, ImportTask
)


# --- Inline для OrderItem ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = True


# --- ModelAdmin Classes ---

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'type', 'company', 'position', 'is_active', 'date_joined')
    list_filter = ('type', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'company')
    search_fields = ('email', 'first_name', 'last_name', 'company', 'position')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'type', 'company', 'position')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'user', 'state')
    list_filter = ('state', 'user')
    search_fields = ('name', 'user__email')


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


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('product_info', 'parameter', 'value')
    list_filter = ('parameter', 'product_info__shop')
    search_fields = ('value', 'parameter__name', 'product_info__product__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'contact')
    list_filter = ('state', 'dt', 'user')
    search_fields = ('user__email', 'id', 'contact__city', 'contact__phone')
    inlines = [OrderItemInline]


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
    readonly_fields = ('key', 'created_at', 'user')


@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at', 'is_processed', 'products_count', 'categories_count', 'parameters_count')
    list_filter = ('is_processed', 'uploaded_at')
    readonly_fields = ('uploaded_at', 'is_processed', 'products_count', 'categories_count', 'parameters_count')
    change_list_template = "admin/import_task_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-yaml/', self.admin_site.admin_view(self.import_yaml_view), name='import_yaml'),
        ]
        return custom_urls + urls

    def import_yaml_view(self, request):
        if request.method == 'POST':
            yaml_file = request.FILES.get('yaml_file')
            if yaml_file:
                try:
                    # Читаем YAML напрямую из загруженного файла (исправлена ошибка с encoding)
                    data = yaml.safe_load(yaml_file.read().decode('utf-8'))

                    # Импортируем данные
                    stats = self._import_data(data)

                    # Создаём запись об импорте
                    ImportTask.objects.create(
                        yaml_file=yaml_file,
                        is_processed=True,
                        products_count=stats['products'],
                        categories_count=stats['categories'],
                        parameters_count=stats['parameters']
                    )

                    self.message_user(
                        request,
                        f'Импорт завершён! Создано: {stats["products"]} товаров, '
                        f'{stats["categories"]} категорий, {stats["parameters"]} параметров.',
                        level=messages.SUCCESS
                    )
                    return redirect('admin:backend_importtask_changelist')

                except Exception as e:
                    self.message_user(request, f'Ошибка импорта: {str(e)}', level=messages.ERROR)
            else:
                self.message_user(request, 'Файл не выбран', level=messages.ERROR)

        return render(request, 'admin/import_yaml_form.html', {
            'title': 'Импорт товаров из YAML',
        })

    def _import_data(self, data):
        """Логика импорта данных из YAML"""
        stats = {'products': 0, 'categories': 0, 'parameters': 0}

        # Получаем или создаём магазин
        shop_name = data.get('shop', 'Default Shop')
        shop, _ = Shop.objects.get_or_create(name=shop_name)

        # Импорт категорий
        categories_data = data.get('categories', [])
        categories_map = {}

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                id=cat_data['id'],
                defaults={'name': cat_data['name']}
            )
            if created:
                stats['categories'] += 1
            category.shops.add(shop)
            categories_map[cat_data['id']] = category

        # Импорт товаров
        goods_data = data.get('goods', [])

        for good in goods_data:
            # Получаем категорию
            category = categories_map.get(good['category'])
            if not category:
                continue

            # Создаём или получаем продукт
            product, _ = Product.objects.get_or_create(
                name=good['name'],
                defaults={'category': category}
            )

            # Создаём ProductInfo
            product_info, _ = ProductInfo.objects.update_or_create(
                external_id=good['id'],
                shop=shop,
                defaults={
                    'product': product,
                    'model': good.get('model', ''),
                    'quantity': good.get('quantity', 0),
                    'price': good.get('price', 0),
                    'price_rrc': good.get('price_rrc', 0),
                }
            )
            stats['products'] += 1

            # Импорт параметров
            parameters = good.get('parameters', {})
            for param_name, param_value in parameters.items():
                parameter, _ = Parameter.objects.get_or_create(name=param_name)
                ProductParameter.objects.update_or_create(
                    product_info=product_info,
                    parameter=parameter,
                    defaults={'value': str(param_value)}
                )
                stats['parameters'] += 1

        return stats