from django.urls import path
from .views import CreateOrderAPI, UserOrdersAPI, AdminOrderListAPI, AdminOrderDetailAPI, AdminOrderUpdateAPI, AdminOrderDeleteAPI, AdminOrderCreateAPI


urlpatterns = [
    path('orders/create/', CreateOrderAPI.as_view(), name='create_order'),
    path('my-orders/', UserOrdersAPI.as_view(), name='user_orders'),
    path('admin/orders/', AdminOrderListAPI.as_view(), name='admin_order_list'),
    path('admin/orders/<int:pk>/', AdminOrderDetailAPI.as_view(), name='admin_order_detail'),
    path('admin/orders/<int:pk>/update/', AdminOrderUpdateAPI.as_view(), name='admin_order_update'),
    path('admin/orders/<int:pk>/delete/', AdminOrderDeleteAPI.as_view(), name='admin_order_delete'),
    path('admin/orders/create/', AdminOrderCreateAPI.as_view(), name='admin_order_create'),
]