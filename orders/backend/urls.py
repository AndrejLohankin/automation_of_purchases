# backend/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('register/', views.RegisterView.as_view(), name='user-register'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('basket/', views.CartView.as_view(), name='cart'),
    path('contacts/', views.AddContactView.as_view(), name='contact-add'),  # POST
    path('contacts/list/', views.ContactListView.as_view(), name='contact-list'),  # GET

    # --- НОВЫЕ ПУТИ ДЛЯ ДЕТАЛЕЙ ---
    path('orders/<int:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('products/<int:product_info_id>/', views.ProductSpecificationView.as_view(), name='product-spec'),
    path('contacts/<int:contact_id>/', views.ContactDetailView.as_view(), name='contact-detail'),
    # --- КОНЕЦ НОВЫХ ПУТЕЙ ДЛЯ ДЕТАЛЕЙ ---

    path('orders/confirm/', views.OrderConfirmationView.as_view(), name='order-confirm'),
    path('orders/history/', views.OrderHistoryView.as_view(), name='order-history'),
    path('admin/trigger-import/', views.trigger_import, name='trigger-import'),

    # --- НОВЫЕ ПУТИ ---
    path('cart/delete/', views.DeleteCartItemView.as_view(), name='cart-delete'),
    path('contacts/detailed/', views.DetailedContactListView.as_view(), name='contacts-detailed'),

    # --- КОНЕЦ НОВЫХ ПУТЕЙ ---

    # --- НОВЫЕ ПУТИ ДЛЯ УДАЛЕНИЯ ---
    path('cart/delete-batch/', views.BatchDeleteCartItemView.as_view(), name='cart-delete-batch'),
    path('cart/clear/', views.ClearCartView.as_view(), name='cart-clear'),
    path('contacts/delete/', views.DeleteContactView.as_view(), name='contact-delete'),
    # --- НОВЫЕ ПУТИ ДЛЯ УПРАВЛЕНИЯ ЗАКАЗАМИ ---
    path('orders/<int:order_id>/status/', views.OrderStatusUpdateView.as_view(), name='order-status-update'),
]