from rest_framework import serializers
from products.models import Product
from .models import Order
from user.serializers import UserSerializer
from products.serializers import ProductSerializers

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    products = ProductSerializers(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'products', 'created_at', 'status']
        read_only_fields = ['id', 'user', 'created_at']

class OrderCreateSerializer(serializers.ModelSerializer):
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )

    class Meta:
        model = Order
        fields = ['product_ids']

    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids')
        user = self.context['request'].user
        order = Order.objects.create(user=user)

        # Проверяем, существуют ли продукты
        products = Product.objects.filter(id__in=product_ids)
        if len(products) != len(product_ids):
            missing_ids = set(product_ids) - set(products.values_list('id', flat=True))
            raise serializers.ValidationError(f"Products with IDs {missing_ids} do not exist.")

        order.products.set(products)
        return order