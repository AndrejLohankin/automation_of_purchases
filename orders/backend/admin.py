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
    list_display = ('id', 'uploaded_at', 'is_processed', 'products_count',
                    'categories_count', 'parameters_count', 'trigger_import_button')
    list_filter = ('is_processed', 'uploaded_at')
    readonly_fields = ('uploaded_at', 'is_processed', 'products_count',
                       'categories_count', 'parameters_count')
    change_list_template = "admin/import_task_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-yaml/', self.admin_site.admin_view(self.import_yaml_view), name='import_yaml'),
        ]
        return custom_urls + urls

    def import_yaml_view(self, request):
        """Только загрузка файла, БЕЗ импорта"""
        if request.method == 'POST':
            yaml_file = request.FILES.get('yaml_file')
            if yaml_file:
                try:
                    # Просто сохраняем файл!
                    import_task = ImportTask.objects.create(
                        yaml_file=yaml_file,
                        is_processed=False,  # <-- False, ещё не обработан
                        products_count=0,
                        categories_count=0,
                        parameters_count=0
                    )

                    self.message_user(
                        request,
                        f'Файл загружен. ID: {import_task.id}. '
                        f'Нажмите "Запустить импорт через Celery" для обработки.',
                        level=messages.SUCCESS
                    )
                    return redirect('admin:backend_importtask_changelist')
                except Exception as e:
                    self.message_user(request, f'Ошибка загрузки: {str(e)}', level=messages.ERROR)
            else:
                self.message_user(request, 'Файл не выбран', level=messages.ERROR)

        return render(request, 'admin/import_yaml_form.html', {
            'title': 'Импорт товаров из YAML',
        })

    def trigger_import_button(self, obj):
        """Кнопка для запуска импорта через Celery"""
        if not obj.is_processed:
            return format_html(
                '<button type="button" class="button" '
                'onclick="triggerImport({0})">Запустить импорт через Celery</button>'
                '<span id="import-status-{0}" style="margin-left: 10px; color: green;"></span>'
                '<script>'
                'function triggerImport(id){{'
                '  fetch("/api/admin/trigger-import/",{{'
                '    method:"POST",'
                '    headers:{{"Content-Type":"application/json","X-CSRFToken":getCookie("csrftoken")}},'
                '    body:JSON.stringify({{import_task_id:id}})'
                '  }})'
                '  .then(r=>r.json())'
                '  .then(d=>{{'
                '    if(d.task_id){{document.getElementById("import-status-"+id).innerHTML="✅ Запущено!";'
                '      setTimeout(()=>location.reload(),2000);'
                '    }}else{{document.getElementById("import-status-"+id).innerHTML="❌ "+d.error;}}'
                '  }});'
                '}}'
                'function getCookie(name){{let v=null;if(document.cookie){{document.cookie.split(";").forEach(c=>{{if(c.trim().startsWith(name+"="))v=decodeURIComponent(c.trim().substring(name.length+1));}});}}return v;}}'
                '</script>',
                obj.id
            )
        return "✅ Обработан через Celery"

    trigger_import_button.short_description = 'Запуск импорта'