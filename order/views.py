import requests
import logging
from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer


class CreateOrderAPI(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Создать новый заказ",
        operation_description="Создаёт новый заказ для аутентифицированного пользователя, принимая массив объектов с ID продуктов, количеством, адресом доставки и комментарием. Отправляет уведомление в Telegram.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_ids"],
            properties={
                "product_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                            "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество продукта"),
                        }
                    ),
                    description="Массив объектов с ID продуктов и их количеством"
                ),
                "address": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Адрес доставки",
                    maxLength=500
                ),
                "comment": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Комментарий к заказу",
                    maxLength=1000
                )
            },
            example={
                "product_ids": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1}
                ],
                "address": "123 Main St, City, Country",
                "comment": "Please deliver after 5 PM"
            }
        ),
        responses={
            201: OrderSerializer,
            400: "Неверные данные или продукты не найдены"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        user = request.user
        total_price = sum(item.quantity * item.product.price for item in order.items.all())
        product_list = "\n".join(
            [f"- {item.product.title} (ID: {item.product.id}, Кол-во: {item.quantity}, Цена: {item.product.price})"
             for item in order.items.all()]
        )
        message = (
            f"<b>🛒 Новый заказ #{order.id}</b>\n\n"
            f"<b>👤 Клиент:</b> {user.name} {user.surname}\n"
            f"<b>📞 Телефон:</b> {user.phone_number}\n"
            f"<b>🏠 Адрес доставки:</b> {order.address or 'Не указан'}\n"
            f"<b>💬 Комментарий:</b> {order.comment or 'Не указан'}\n"
            f"<b>📦 Продукты:</b>\n{product_list}\n\n"
            f"<b>💵 Общая сумма:</b> {total_price}\n"
            f"<b>📅 Дата:</b> {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"<b>📢 Статус:</b> {order.status}"
        )

        telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': settings.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(telegram_url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Не удалось отправить сообщение в Telegram: {e}")

        return Response(OrderSerializer(order).data, status=201)


class UserOrdersAPI(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Получить список заказов пользователя",
        operation_description="Возвращает список всех заказов текущего аутентифицированного пользователя.",
        responses={
            200: openapi.Response(
                description="Список заказов",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID заказа"),
                            "user": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                                    "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                                    "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                                    "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                                    "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя")
                                }
                            ),
                            "items": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "product": openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                                                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                                                "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Цена продукта"),
                                            }
                                        ),
                                        "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество продукта")
                                    }
                                ),
                                description="Список продуктов в заказе"
                            ),
                            "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="Дата создания заказа"),
                            "status": openapi.Schema(type=openapi.TYPE_STRING, description="Статус заказа"),
                            "address": openapi.Schema(type=openapi.TYPE_STRING, description="Адрес доставки", nullable=True),
                            "comment": openapi.Schema(type=openapi.TYPE_STRING, description="Комментарий к заказу", nullable=True)
                        }
                    )
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class AdminOrderListAPI(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().order_by('-created_at')

    @swagger_auto_schema(
        operation_summary="Получить список всех заказов (Админ)",
        operation_description="Возвращает список всех заказов в системе для администратора, отсортированных по дате создания (от новых к старым).",
        responses={
            200: OrderSerializer(many=True),
            403: "Недостаточно прав доступа"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminOrderDetailAPI(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all()

    @swagger_auto_schema(
        operation_summary="Получить детали заказа (Админ)",
        operation_description="Возвращает подробную информацию о заказе по его ID для администратора.",
        responses={
            200: OrderSerializer,
            403: "Недостаточно прав доступа",
            404: "Заказ не найден"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminOrderUpdateAPI(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all()

    @swagger_auto_schema(
        operation_summary="Обновить заказ (Админ)",
        operation_description="Позволяет администратору обновить данные заказа, например, изменить статус, адрес доставки или комментарий.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['pending', 'shipping', 'delivered', 'cancelled'],
                    description="Статус заказа"
                ),
                "address": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Адрес доставки",
                    maxLength=500
                ),
                "comment": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Комментарий к заказу",
                    maxLength=1000
                ),
            },
            example={
                "status": "shipping",
                "address": "123 Main St, City, Country",
                "comment": "Updated comment"
            }
        ),
        responses={
            200: OrderSerializer,
            400: "Неверные данные",
            403: "Недостаточно прав доступа",
            404: "Заказ не найден"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class AdminOrderDeleteAPI(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all()

    @swagger_auto_schema(
        operation_summary="Удалить заказ (Админ)",
        operation_description="Позволяет администратору удалить заказ по его ID.",
        responses={
            204: "Заказ успешно удален",
            403: "Недостаточно прав доступа",
            404: "Заказ не найден"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AdminOrderCreateAPI(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Создать новый заказ (Админ)",
        operation_description="Позволяет администратору создать новый заказ от имени пользователя, указав массив объектов с ID продуктов, количеством, адресом доставки и комментарием.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_ids", "user_id"],
            properties={
                "product_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                            "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество продукта"),
                        }
                    ),
                    description="Массив объектов с ID продуктов и их количеством"
                ),
                "user_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID пользователя, для которого создается заказ"
                ),
                "address": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Адрес доставки",
                    maxLength=500
                ),
                "comment": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Комментарий к заказу",
                    maxLength=1000
                )
            },
            example={
                "product_ids": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1}
                ],
                "user_id": 1,
                "address": "123 Main St, City, Country",
                "comment": "Admin created order"
            }
        ),
        responses={
            201: OrderSerializer,
            400: "Неверные данные или продукты/пользователь не найдены",
            403: "Недостаточно прав доступа"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        user = order.user
        total_price = sum(item.quantity * item.product.price for item in order.items.all())
        product_list = "\n".join(
            [f"- {item.product.title} (ID: {item.product.id}, Кол-во: {item.quantity}, Цена: {item.product.price})"
             for item in order.items.all()]
        )
        message = (
            f"<b>🛒 Новый заказ #{order.id} (Создан админом)</b>\n\n"
            f"<b>👤 Клиент:</b> {user.name} {user.surname}\n"
            f"<b>📞 Телефон:</b> {user.phone_number}\n"
            f"<b>🏠 Адрес доставки:</b> {order.address or 'Не указан'}\n"
            f"<b>💬 Комментарий:</b> {order.comment or 'Не указан'}\n"
            f"<b>📦 Продукты:</b>\n{product_list}\n\n"
            f"<b>💵 Общая сумма:</b> {total_price}\n"
            f"<b>📅 Дата:</b> {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"<b>📢 Статус:</b> {order.status}"
        )

        telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': settings.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(telegram_url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Не удалось отправить сообщение в Telegram: {e}")

        return Response(OrderSerializer(order).data, status=201)