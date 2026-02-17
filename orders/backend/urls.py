# backend/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('register/', views.RegisterView.as_view(), name='user-register'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('basket/', views.CartView.as_view(), name='cart'),
    path('contacts/', views.AddContactView.as_view(), name='contact-add'),  # <-- POST
    path('contacts/list/', views.ContactListView.as_view(), name='contact-list'),  # <-- GET
    path('orders/confirm/', views.OrderConfirmationView.as_view(), name='order-confirm'),
    path('orders/history/', views.OrderHistoryView.as_view(), name='order-history'),
    path('admin/trigger-import/', views.trigger_import, name='trigger-import'),
    # path('shops/', views.ShopListView.as_view(), name='shop-list'), # Если нужно
    # path('categories/', views.CategoryListView.as_view(), name='category-list'), # Если нужно
    # --- НОВЫЕ ПУТИ ---
    path('cart/delete/', views.DeleteCartItemView.as_view(), name='cart-delete'),
    path('contacts/detailed/', views.DetailedContactListView.as_view(), name='contacts-detailed'),
    path('contacts/<int:contact_id/', views.ContactDetailView.as_view(), name='contact-detail'),
    # --- КОНЕЦ НОВЫХ ПУТЕЙ ---
    # --- НОВЫЕ ПУТИ ДЛЯ УДАЛЕНИЯ ---
    path('cart/delete-batch/', views.BatchDeleteCartItemView.as_view(), name='cart-delete-batch'),
    path('cart/clear/', views.ClearCartView.as_view(), name='cart-clear'),
    # --- КОНЕЦ НОВЫХ ПУТЕЙ ДЛЯ УДАЛЕНИЯ ---
]