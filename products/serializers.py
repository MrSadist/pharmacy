from rest_framework import serializers
from .models import Product, Comment, Category


class RecursiveCategorySerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = CategorySerializers(value, context=self.context)
        return serializer.data

class CategorySerializers(serializers.ModelSerializer):
    children = RecursiveCategorySerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name_uz', 'name_ru', 'name_en', 'parent', 'children']


class CommentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'product', 'text', 'rating', 'created_at']


class ProductSerializers(serializers.ModelSerializer):
    comments = CommentSerializers(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    category = CategorySerializers(read_only=True)


    class Meta:
        model=Product
        fields=['id', 'title','description_uz', 'description_ru', 'description_en', 'instruction_uz', 'instruction_ru', 'instruction_en', 'price', 'old_price', 'link', 'total', 'comments', 'average_rating', 'category', 'new']

