from rest_framework import serializers
from products.models import Product
from products.serializers import ProductSerializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializers(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']
        read_only_fields = ['id', 'total_price']

    def get_total_price(self, obj):
        return obj.quantity * obj.product.price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())


class CartItemAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Продукт с ID {value} не существует.")
        return value

    def validate(self, data):
        product = Product.objects.get(id=data['product_id'])
        if product.total < data['quantity']:
            raise serializers.ValidationError(
                f"Недостаточно товара: доступно {product.total}, запрошено {data['quantity']}."
            )
        return data

    def create(self, validated_data):
        cart = self.context['cart']
        product = Product.objects.get(id=validated_data['product_id'])
        quantity = validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={'quantity': quantity}
        )
        if not created:
            new_quantity = cart_item.quantity + quantity
            if product.total < new_quantity:
                raise serializers.ValidationError(
                    f"Недостаточно товара: доступно {product.total}, запрошено {new_quantity}."
                )
            cart_item.quantity = new_quantity
            cart_item.save()

        return cart_item


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        product = self.instance.product
        if product.total < value:
            raise serializers.ValidationError(
                f"Недостаточно товара: доступно {product.total}, запрошено {value}."
            )
        return value

    def update(self, instance, validated_data):
        instance.quantity = validated_data['quantity']
        instance.save()
        return instance