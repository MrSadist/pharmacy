from django.urls import path
from .views import CreateOrderAPI, UserOrdersAPI

urlpatterns = [
    path('create/', CreateOrderAPI.as_view(), name='create_order'),
    path('my-orders/', UserOrdersAPI.as_view(), name='user_orders'),
]