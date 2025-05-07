from rest_framework import serializers
from .models import Product, Comment, Category, Tag, AGE_RANGE_CHOICES, FAQ
from user.serializers import UserSerializer


class RecursiveCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name_uz', 'name_ru', 'name_en', 'children', 'image']

    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        children = obj.children.all()
        serializer = RecursiveCategorySerializer(children, many=True, context=self.context)
        return serializer.data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name_uz', 'name_ru', 'name_en']


class TagDetailSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ('id', 'name_uz', 'name_ru', 'name_en', 'products')

    def get_products(self, obj):
        products = Product.objects.filter(tags=obj)
        return ProductSerializers(products, many=True).data


class CategorySerializers(serializers.ModelSerializer):
    children = RecursiveCategorySerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name_uz', 'name_ru', 'name_en', 'parent', 'children', 'image']


class CommentSerializers(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'text', 'rating', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate_rating(self, value):
        if not 1.0 <= value <= 5.0:
            raise serializers.ValidationError("Рейтинг должен быть от 1.0 до 5.0.")
        return value


class ProductSerializers(serializers.ModelSerializer):
    comments = CommentSerializers(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=False
    )
    tags = TagSerializer(many=True, read_only=True, required=False)  # Для отображения тегов
    tags_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True, required=False ,source='tags'
    )
    age_range = serializers.ChoiceField(
        choices=AGE_RANGE_CHOICES,
        required=False,
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        category = instance.category
        if category:
            representation['category'] = CategorySerializers(category, context=self.context).data
        # representation['age_range'] = dict(Product.AGE_RANGE_CHOICES).get(instance.age_range, instance.age_range)
        return representation


    class Meta:
        model=Product
        fields=['id', 'title','description_uz', 'description_ru', 'description_en', 'instruction_uz', 'instruction_ru', 'instruction_en', 'illness_uz', 'illness_ru', 'illness_en', 'composition_uz', 'composition_ru', 'composition_en', 'price', 'old_price', 'links', 'total', 'comments', 'average_rating', 'category', 'new', 'tags', 'tags_ids', 'age_range',]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question_uz', 'question_ru', 'question_en', 'answer_uz', 'answer_ru', 'answer_en',]
