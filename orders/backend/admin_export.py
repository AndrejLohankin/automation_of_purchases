# backend/admin_export.py

from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
import yaml
from .models import (
    User, Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken, ImportTask
)
from datetime import datetime
from django.http import StreamingHttpResponse

@admin.register(ProductInfo)
class ProductInfoExportAdmin(admin.ModelAdmin):
    """Административная панель для экспорта товаров"""
    list_display = ('product', 'shop', 'external_id', 'model', 'price', 'quantity')
    list_filter = ('shop', 'product__category')
    search_fields = ('product__name', 'model', 'external_id', 'shop__name')
    actions = ['export_selected_products', 'export_all_products']
    change_list_template = 'admin/product_info_export_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export/', self.admin_site.admin_view(self.export_view), name='export_products'),
        ]
        return custom_urls + urls

    def export_view(self, request):
        """Экспорт товаров с фильтрацией"""
        # Фильтрация
        shop_id = request.GET.get('shop_id')
        category_id = request.GET.get('category_id')
        search = request.GET.get('search')
        format = request.GET.get('format', 'yaml')

        # Фильтрация товаров
        queryset = ProductInfo.objects.select_related('product', 'shop').prefetch_related(
            'product_parameters__parameter'
        )

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        if search:
            queryset = queryset.filter(product__name__icontains=search)

        # Создаем структуру данных для экспорта
        export_data = {
            'shop': 'Default Shop',
            'categories': [],
            'goods': []
        }

        # Собираем уникальные категории
        categories_set = set()
        for product_info in queryset:
            if product_info.product.category:
                categories_set.add(product_info.product.category)

        # Добавляем категории
        for category in categories_set:
            export_data['categories'].append({
                'id': category.id,
                'name': category.name
            })

        # Добавляем товары
        for product_info in queryset:
            # Собираем параметры товара
            parameters = {}
            for param in product_info.product_parameters.all():
                parameters[param.parameter.name] = param.value

            export_data['goods'].append({
                'id': product_info.external_id,
                'name': product_info.product.name,
                'category': product_info.product.category.id if product_info.product.category else None,
                'quantity': product_info.quantity,
                'price': product_info.price,
                'parameters': parameters
            })

        # Форматируем в выбранный формат
        if format == 'yaml':
            # Язык описания
            if 'goods' in export_data:
                for item in export_data['goods']:
                    if item['category'] is None:
                        item['category'] = 0
            yaml_data = yaml.dump(export_data, sort_keys=False, indent=2)
            content_type = 'application/x-yaml; charset=utf-8'
            filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
        elif format == 'json':
            import json
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            content_type = 'application/json; charset=utf-8'
            filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        else:
            return render(request, 'admin/export_error.html', {
                'error': 'Unsupported format',
                'formats': ['yaml', 'json']
            }, status=400)

        # Создаем поток для файла
        response = StreamingHttpResponse(
            yaml_data if format == 'yaml' else json_data,
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    def export_selected_products(self, request, queryset):
        """Экспортировать выбранные товары"""
        # Создаем структуру данных для экспорта
        export_data = {
            'shop': 'Default Shop',
            'categories': [],
            'goods': []
        }

        # Собираем уникальные категории
        categories_set = set()
        for product_info in queryset:
            if product_info.product.category:
                categories_set.add(product_info.product.category)

        # Добавляем категории
        for category in categories_set:
            export_data['categories'].append({
                'id': category.id,
                'name': category.name
            })

        # Добавляем товары
        for product_info in queryset:
            # Собираем параметры товара
            parameters = {}
            for param in product_info.product_parameters.all():
                parameters[param.parameter.name] = param.value

            export_data['goods'].append({
                'id': product_info.external_id,
                'name': product_info.product.name,
                'category': product_info.product.category.id if product_info.product.category else None,
                'quantity': product_info.quantity,
                'price': product_info.price,
                'parameters': parameters
            })

        # Форматируем в YAML
        yaml_data = yaml.dump(export_data, sort_keys=False, indent=2)
        content_type = 'application/x-yaml; charset=utf-8'
        filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'

        # Создаем поток для файла
        response = StreamingHttpResponse(
            yaml_data,
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    def export_all_products(self, request, queryset):
        """Экспортировать все товары"""
        # Используем уже существующий метод для экспорта всех товаров
        return self.export_selected_products(request, ProductInfo.objects.all())