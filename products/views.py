from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Product, Comment, Category
from .serializers import ProductSerializers, CommentSerializers, CategorySerializers
from django.db.models import Avg
from rest_framework.filters import SearchFilter

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializers

    @swagger_auto_schema(
        operation_summary="Получить список категорий",
        operation_description="Возвращает список всех категорий с их названиями на трёх языках (узбекский, русский, английский).",
        responses={200: CategorySerializers(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные категории",
        operation_description="Возвращает данные конкретной категории по её ID, включая названия на трёх языках.",
        responses={200: CategorySerializers()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новую категорию",
        operation_description="Создаёт новую категорию с названиями на трёх языках.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name_uz", "name_ru", "name_en"],
            properties={
                "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке"),
                "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке"),
                "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке")
            },
            example={
                "name_uz": "Электроника",
                "name_ru": "Электроника",
                "name_en": "Electronics"
            }
        ),
        responses={201: CategorySerializers()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить данные категории (полное обновление)",
        operation_description="Обновляет данные указанной категории по её ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке"),
                "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке"),
                "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке")
            },
            example={
                "name_uz": "Бытовая техника",
                "name_ru": "Бытовая техника",
                "name_en": "Home Appliances"
            }
        ),
        responses={200: CategorySerializers()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные категории",
        operation_description="Частично обновляет данные указанной категории по её ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке"),
                "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке"),
                "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке")
            },
            example={
                "name_ru": "Обновлённая бытовая техника"
            }
        ),
        responses={200: CategorySerializers()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить категорию",
        operation_description="Удаляет категорию по её ID.",
        responses={204: "Нет содержимого"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers
    filter_backends = [SearchFilter]
    search_fields = [
        'title',
        'description_uz',
        'description_ru',
        'description_en',
        'instruction_uz',
        'instruction_ru',
        'instruction_en',
    ]

    def get_queryset(self):
        base_queryset = Product.objects.annotate(
            average_rating=Avg('comments__rating')
        )
        return self.get_filtered_queryset(base_queryset)

    def get_filtered_queryset(self, base_queryset):
        params = self.request.query_params

        has_old_price = params.get('has_old_price')
        if has_old_price == 'true':
            base_queryset = base_queryset.filter(old_price__isnull=False)
        elif has_old_price == 'false':
            base_queryset = base_queryset.filter(old_price__isnull=True)

        price_min = params.get('price_min')
        if price_min:
            base_queryset = base_queryset.filter(price__gte=price_min)

        price_max = params.get('price_max')
        if price_max:
            base_queryset = base_queryset.filter(price__lte=price_max)

        average_rating = params.get('average_rating')
        if average_rating:
            base_queryset = base_queryset.filter(average_rating__gte=average_rating)

        new_product = self.request.query_params.get('new')
        if new_product is not None:
            if new_product.lower() == 'true':
                base_queryset = base_queryset.filter(new=True)
            elif new_product.lower() == 'false':
                base_queryset = base_queryset.filter(new=False)

        return base_queryset

    @swagger_auto_schema(
        operation_summary="Получить список продуктов",
        operation_description="Возвращает список продуктов с возможностью фильтрации по цене, наличию старой цены, среднему рейтингу и поиску по названию или описанию.",
        manual_parameters=[
            openapi.Parameter('has_old_price', openapi.IN_QUERY, description="Фильтр по наличию старой цены (true/false)", type=openapi.TYPE_STRING),
            openapi.Parameter('new', openapi.IN_QUERY,description="Фильтр по статусу (true/false)", type=openapi.TYPE_STRING),
            openapi.Parameter('price_min', openapi.IN_QUERY, description="Минимальная цена", type=openapi.TYPE_INTEGER),
            openapi.Parameter('price_max', openapi.IN_QUERY, description="Максимальная цена", type=openapi.TYPE_INTEGER),
            openapi.Parameter('average_rating', openapi.IN_QUERY, description="Минимальный средний рейтинг", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по названию, описанию или инструкции", type=openapi.TYPE_STRING)
        ],
        responses={200: ProductSerializers(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные продукта",
        operation_description="Возвращает данные конкретного продукта по его ID, включая название, описание, инструкции на трёх языках, цену и средний рейтинг.",
        responses={200: ProductSerializers()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новый продукт",
        operation_description="Создаёт новый продукт с названием, описанием, инструкциями на трёх языках, ценой и категорией.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["title", "description_uz", "description_ru", "description_en", "instruction_uz", "instruction_ru", "instruction_en", "price"],
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                "description_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на узбекском языке"),
                "description_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на русском языке"),
                "description_en": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на английском языке"),
                "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на узбекском языке"),
                "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на русском языке"),
                "instruction_en": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на английском языке"),
                "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Цена продукта"),
                "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Старая цена продукта (опционально)"),
                "category": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории"),
                "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="true/false"),
            },
            example={
                "title": "Смартфон",
                "description_uz": "Yangi smartfon",
                "description_ru": "Новый смартфон",
                "description_en": "New smartphone",
                "instruction_uz": "Foydalanish bo'yicha ko'rsatmalar",
                "instruction_ru": "Инструкции по использованию",
                "instruction_en": "Usage instructions",
                "price": 5000000,
                "old_price": 6000000,
                "category": 1,
                "new": True
            }
        ),
        responses={201: ProductSerializers()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить данные продукта (полное обновление)",
        operation_description="Обновляет данные указанного продукта по его ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                "description_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на узбекском языке"),
                "description_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на русском языке"),
                "description_en": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на английском языке"),
                "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на узбекском языке"),
                "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на русском языке"),
                "instruction_en": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на английском языке"),
                "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Цена продукта"),
                "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Старая цена продукта (опционально)"),
                "category": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории"),
                "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="true/false")
            },
            example={
                "title": "Обновлённый смартфон",
                "description_uz": "Yangi smartfon (yangilangan)",
                "description_ru": "Новый смартфон (обновлённый)",
                "description_en": "New smartphone (updated)",
                "instruction_uz": "Yangilangan ko'rsatmalar",
                "instruction_ru": "Обновлённые инструкции",
                "instruction_en": "Updated instructions",
                "price": 5500000,
                "old_price": 6500000,
                "category": 1,
                "new":True
            }
        ),
        responses={200: ProductSerializers()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные продукта",
        operation_description="Частично обновляет данные указанного продукта по его ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                "description_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на узбекском языке"),
                "description_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на русском языке"),
                "description_en": openapi.Schema(type=openapi.TYPE_STRING, description="Описание на английском языке"),
                "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на узбекском языке"),
                "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на русском языке"),
                "instruction_en": openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция на английском языке"),
                "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Цена продукта"),
                "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Старая цена продукта (опционально)"),
                "category": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории"),
                "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="true/false")
            },
            example={
                "price": 5200000
            }
        ),
        responses={200: ProductSerializers()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить продукт",
        operation_description="Удаляет продукт по его ID.",
        responses={204: "Нет содержимого"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить продукты по категории",
        operation_description="Возвращает список продуктов в указанной категории с возможностью фильтрации по цене, наличию старой цены и среднему рейтингу.",
        manual_parameters=[
            openapi.Parameter('category_id', openapi.IN_PATH, description="ID категории", type=openapi.TYPE_INTEGER),
            openapi.Parameter('has_old_price', openapi.IN_QUERY, description="Фильтр по наличию старой цены (true/false)", type=openapi.TYPE_STRING),
            openapi.Parameter('price_min', openapi.IN_QUERY, description="Минимальная цена", type=openapi.TYPE_INTEGER),
            openapi.Parameter('price_max', openapi.IN_QUERY, description="Максимальная цена", type=openapi.TYPE_INTEGER),
            openapi.Parameter('average_rating', openapi.IN_QUERY, description="Минимальный средний рейтинг", type=openapi.TYPE_INTEGER)
        ],
        responses={200: ProductSerializers(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='by_category/(?P<category_id>[^/.]+)')
    def by_category(self, request, category_id=None):
        queryset = Product.objects.filter(category_id=category_id).annotate(
            average_rating=Avg('comments__rating')
        )
        filtered_qs = self.get_filtered_queryset(queryset)
        serializer = self.get_serializer(filtered_qs, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializers

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        if product_id:
            return Comment.objects.filter(product_id=product_id)
        return Comment.objects.all()

    @swagger_auto_schema(
        operation_summary="Получить список комментариев",
        operation_description="Возвращает список комментариев. Если указан product_id, возвращает комментарии для конкретного продукта.",
        responses={200: CommentSerializers(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные комментария",
        operation_description="Возвращает данные конкретного комментария по его ID.",
        responses={200: CommentSerializers()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новый комментарий",
        operation_description="Создаёт новый комментарий для указанного продукта.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product", "text", "rating"],
            properties={
                "product": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                "text": openapi.Schema(type=openapi.TYPE_STRING, description="Текст комментария"),
                "rating": openapi.Schema(type=openapi.TYPE_INTEGER, description="Рейтинг (от 1 до 5)")
            },
            example={
                "product": 1,
                "text": "Отличный продукт!",
                "rating": 5
            }
        ),
        responses={
            201: CommentSerializers(),
            400: "Продукт не найден"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        serializer.save(product=product)

    @swagger_auto_schema(
        operation_summary="Обновить комментарий (полное обновление)",
        operation_description="Обновляет текст и рейтинг указанного комментария по его ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "text": openapi.Schema(type=openapi.TYPE_STRING, description="Текст комментария"),
                "rating": openapi.Schema(type=openapi.TYPE_INTEGER, description="Рейтинг (от 1 до 5)")
            },
            example={
                "text": "Обновлённый комментарий",
                "rating": 4
            }
        ),
        responses={200: CommentSerializers()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить комментарий",
        operation_description="Частично обновляет текст или рейтинг указанного комментария по его ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "text": openapi.Schema(type=openapi.TYPE_STRING, description="Текст комментария"),
                "rating": openapi.Schema(type=openapi.TYPE_INTEGER, description="Рейтинг (от 1 до 5)")
            },
            example={
                "rating": 3
            }
        ),
        responses={200: CommentSerializers()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить комментарий",
        operation_description="Удаляет комментарий по его ID.",
        responses={204: "Нет содержимого"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)