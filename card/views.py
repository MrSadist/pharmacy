import logging
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from order.models import Order, OrderItem
from order.serializers import OrderSerializer
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemAddSerializer, CartItemUpdateSerializer


class CartAPI(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @swagger_auto_schema(
        operation_summary="Получить корзину пользователя",
        operation_description="Возвращает содержимое корзины текущего аутентифицированного пользователя, включая список продуктов и общую стоимость.",
        responses={
            200: CartSerializer,
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CartItemAddAPI(generics.CreateAPIView):
    serializer_class = CartItemAddSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        context['cart'] = cart
        return context

    @swagger_auto_schema(
        operation_summary="Добавить продукт в корзину",
        operation_description="Добавляет продукт в корзину пользователя. Если продукт уже есть, увеличивает его количество.",
        request_body=CartItemAddSerializer,
        responses={
            201: CartSerializer,
            400: "Неверные данные или продукт не найден",
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cart = Cart.objects.get(user=self.request.user)
        return Response(CartSerializer(cart).data, status=201)


class CartItemUpdateAPI(generics.UpdateAPIView):
    serializer_class = CartItemUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Обновить количество продукта в корзине",
        operation_description="Обновляет количество указанного продукта в корзине пользователя.",
        request_body=CartItemUpdateSerializer,
        responses={
            200: CartSerializer,
            404: "Элемент корзины не найден",
        }
    )
    def patch(self, request, *args, **kwargs):
        response = super().patch(request, *args, **kwargs)
        cart = Cart.objects.get(user=self.request.user)
        return Response(CartSerializer(cart).data)


class CartItemDeleteAPI(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Удалить продукт из корзины",
        operation_description="Удаляет указанный продукт из корзины пользователя.",
        responses={
            204: "Продукт успешно удален",
            404: "Элемент корзины не найден",
        }
    )
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        cart = Cart.objects.get(user=self.request.user)
        return Response(CartSerializer(cart).data, status=200)


class CartCheckoutAPI(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Создать заказ из корзины",
        operation_description="Создаёт заказ на основе содержимого корзины пользователя, включая адрес доставки и комментарий, и очищает корзину после создания заказа.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
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
                "address": "123 Main St, City, Country",
                "comment": "Please deliver after 5 PM"
            }
        ),
        responses={
            201: OrderSerializer,
            400: "Корзина пуста или продукты не найдены",
        }
    )
    def post(self, request, *args, **kwargs):
        cart = get_object_or_404(Cart, user=self.request.user)
        if not cart.items.exists():
            raise serializers.ValidationError("Корзина пуста.")

        for item in cart.items.all():
            if item.product.total < item.quantity:
                raise serializers.ValidationError(
                    f"Недостаточно товара для продукта ID {item.product.id}: "
                    f"доступно {item.product.total}, запрошено {item.quantity}."
                )

        address = request.data.get('address', '')
        comment = request.data.get('comment', '')

        order = Order.objects.create(
            user=self.request.user,
            address=address,
            comment=comment
        )
        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity
            )
            for item in cart.items.all()
        ]
        OrderItem.objects.bulk_create(order_items)

        total_price = sum(item.quantity * item.product.price for item in cart.items.all())
        product_list = "\n".join(
            [f"- {item.product.title} (ID: {item.product.id}, Кол-во: {item.quantity}, Цена: {item.product.price})"
             for item in cart.items.all()]
        )
        message = (
            f"<b>🛒 Новый заказ #{order.id}</b>\n\n"
            f"<b>👤 Клиент:</b> {self.request.user.name} {self.request.user.surname}\n"
            f"<b>📞 Телефон:</b> {self.request.user.phone_number}\n"
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

        cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=201)