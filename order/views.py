import requests
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
        operation_description="Создаёт новый заказ для аутентифицированного пользователя, принимая массив ID продуктов. После создания отправляет уведомление в Telegram-группу.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_ids"],
            properties={
                "product_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Массив ID продуктов"
                )
            },
            example={
                "product_ids": [1, 2]
            }
        ),
        responses={
            201: openapi.Response(
                description="Заказ успешно создан",
                schema=openapi.Schema(
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
                        "products": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                                    "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                                    "description_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на узбекском языке"),
                                    "description_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на русском языке"),
                                    "description_en": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на английском языке"),
                                    "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на узбекском языке"),
                                    "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на русском языке"),
                                    "instruction_en": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на английском языке"),
                                    "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Цена продукта"),
                                    "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True, description="Старая цена продукта (может быть null)"),
                                    "category": openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории"),
                                            "parent": openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                nullable=True,
                                                properties={
                                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID родительской категории"),
                                                    "parent": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True, description="Рекурсивное поле для родительской категории"),
                                                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на выбранном языке"),
                                                    "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке"),
                                                    "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке"),
                                                    "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке")
                                                },
                                                description="Родительская категория (может быть null)"
                                            ),
                                            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на выбранном языке"),
                                            "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке"),
                                            "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке"),
                                            "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке")
                                        },
                                        description="Категория продукта"
                                    ),
                                    "link": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING),
                                        nullable=True,
                                        description="Список ссылок (может быть пустым)"
                                    ),
                                    "total": openapi.Schema(type=openapi.TYPE_INTEGER, description="Общее количество продукта"),
                                    "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, nullable=True, description="Является ли продукт новым (может быть null)")
                                }
                            ),
                            description="Список продуктов в заказе"
                        ),
                        "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="Дата создания заказа"),
                        "status": openapi.Schema(type=openapi.TYPE_STRING, description="Статус заказа")
                    }
                )
            ),
            400: "Неверные данные или продукты не найдены"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Отправка уведомления в Telegram
        user = request.user
        products = order.products.all()
        total_price = sum(product.price for product in products)
        product_list = "\n".join([f"- {product.title} (ID: {product.id}, Price: {product.price})" for product in products])
        message = (
            f"<b>🛒 Новый заказ #{order.id}</b>\n\n"
            f"<b>👤 Клиент:</b> {user.name} {user.surname}\n"
            f"<b>📞 Телефон:</b> {user.phone_number}\n"
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
            print(f"Failed to send Telegram message: {e}")

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
                            "products": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                                        "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                                        "description_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на узбекском языке"),
                                        "description_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на русском языке"),
                                        "description_en": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на английском языке"),
                                        "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на узбекском языке"),
                                        "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на русском языке"),
                                        "instruction_en": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на английском языке"),
                                        "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Цена продукта"),
                                        "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True, description="Старая цена продукта (может быть null)"),
                                        "category": openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории"),
                                                "parent": openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    nullable=True,
                                                    properties={
                                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID родительской категории"),
                                                        "parent": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True, description="Рекурсивное поле для родительской категории"),
                                                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на выбранном языке"),
                                                        "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке"),
                                                        "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке"),
                                                        "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке")
                                                    },
                                                    description="Родительская категория (может быть null)"
                                                ),
                                                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на выбранном языке"),
                                                "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке"),
                                                "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке"),
                                                "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке")
                                            },
                                            description="Категория продукта"
                                        ),
                                        "link": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_STRING),
                                            nullable=True,
                                            description="Список ссылок (может быть пустым)"
                                        ),
                                        "total": openapi.Schema(type=openapi.TYPE_INTEGER, description="Общее количество продукта"),
                                        "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, nullable=True, description="Является ли продукт новым (может быть null)")
                                    }
                                ),
                                description="Список продуктов в заказе"
                            ),
                            "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="Дата создания заказа"),
                            "status": openapi.Schema(type=openapi.TYPE_STRING, description="Статус заказа")
                        }
                    )
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)