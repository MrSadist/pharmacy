from django.shortcuts import get_object_or_404
from rest_framework import serializers
from products.models import Product
from .models import Order, OrderItem
from user.serializers import UserSerializer
from products.serializers import ProductSerializers
from user.models import CustomUser
from django.db import transaction


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializers(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'product_id', 'quantity']
        read_only_fields = ['product']


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'created_at', 'status', 'address', 'comment']
        read_only_fields = ['id', 'user', 'created_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    product_ids = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            required=True
        ),
        write_only=True,
        required=True
    )
    user_id = serializers.IntegerField(write_only=True, required=False)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = ['product_ids', 'user_id', 'address', 'comment']

    def validate_product_ids(self, value):
        product_ids = [item['product_id'] for item in value]
        products = Product.objects.filter(id__in=product_ids)

        if len(products) != len(product_ids):
            missing_ids = set(product_ids) - set(products.values_list('id', flat=True))
            raise serializers.ValidationError(f"Продукты с ID {missing_ids} не существуют.")

        for item in value:
            product = Product.objects.get(id=item['product_id'])
            if product.total < item['quantity']:
                raise serializers.ValidationError(
                    f"Недостаточно товара для продукта ID {item['product_id']}: "
                    f"доступно {product.total}, запрошено {item['quantity']}."
                )
            if item['quantity'] <= 0:
                raise serializers.ValidationError(
                    f"Количество для продукта ID {item['product_id']} должно быть больше 0."
                )
        return value

    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids')
        user_id = validated_data.get('user_id')
        address = validated_data.pop('address', '')
        comment = validated_data.pop('comment', '')

        if user_id:
            user = get_object_or_404(CustomUser, id=user_id)
        else:
            user = self.context['request'].user

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                address=address,
                comment=comment
            )

            order_items = []
            for item in product_ids:
                product = Product.objects.select_for_update().get(id=item['product_id'])
                product.total -= item['quantity']
                if product.total < 0:
                    raise serializers.ValidationError(
                        f"Недостаточно товара для продукта ID {item['product_id']}: "
                        f"доступно {product.total + item['quantity']}, запрошено {item['quantity']}."
                    )
                product.save()

                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=item['quantity']
                    )
                )

            OrderItem.objects.bulk_create(order_items)

        return order