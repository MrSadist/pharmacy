from django.urls import path
from .views import CartAPI, CartItemAddAPI, CartItemUpdateAPI, CartItemDeleteAPI, CartCheckoutAPI

urlpatterns = [
    path('cart/', CartAPI.as_view(), name='cart-detail'),
    path('cart/add/', CartItemAddAPI.as_view(), name='cart-item-add'),
    path('cart/update/<int:pk>/', CartItemUpdateAPI.as_view(), name='cart-item-update'),
    path('cart/delete/<int:pk>/', CartItemDeleteAPI.as_view(), name='cart-item-delete'),
    path('cart/checkout/', CartCheckoutAPI.as_view(), name='cart-checkout'),
]