from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Product, Comment, Category, Tag, FAQ
from .serializers import ProductSerializers, CommentSerializers, CategorySerializers, TagSerializer, \
    TagDetailSerializer, FAQSerializer
from django.db.models import Avg
from .filters import CustomSearchFilter, ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TagDetailSerializer
        return TagSerializer

    @swagger_auto_schema(
        operation_description="Получить тег по ID вместе с медицинскими препаратами, связанными с ним, включая их параметры.",
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID тега"),
                'name_uz': openapi.Schema(type=openapi.TYPE_STRING, description="Название тега на узбекском"),
                'name_ru': openapi.Schema(type=openapi.TYPE_STRING, description="Название тега на русском"),
                'name_en': openapi.Schema(type=openapi.TYPE_STRING, description="Название тега на английском"),
                'products': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                            'title': openapi.Schema(type=openapi.TYPE_STRING, description="Название медицинского препарата"),
                            'description_uz': openapi.Schema(type=openapi.TYPE_STRING, description="Описание препарата на узбекском языке"),
                            'description_ru': openapi.Schema(type=openapi.TYPE_STRING, description="Описание препарата на русском языке"),
                            'description_en': openapi.Schema(type=openapi.TYPE_STRING, description="Описание препарата на английском языке"),
                            'instruction_uz': openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция по применению на узбекском языке"),
                            'instruction_ru': openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция по применению на русском языке"),
                            'instruction_en': openapi.Schema(type=openapi.TYPE_STRING, description="Инструкция по применению на английском языке"),
                            'illness_uz': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING),
                                description="Перечень заболеваний для лечения (узбекский)",
                                nullable=True
                            ),
                            'illness_ru': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING),
                                description="Перечень заболеваний для лечения (русский)",
                                nullable=True
                            ),
                            'illness_en': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING),
                                description="Перечень заболеваний для лечения (английский)",
                                nullable=True
                            ),
                            'composition_uz': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING),
                                description="Состав препарата (узбекский)",
                                nullable=True
                            ),
                            'composition_ru': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING),
                                description="Состав препарата (русский)",
                                nullable=True
                            ),
                            'composition_en': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING),
                                description="Состав препарата (английский)",
                                nullable=True
                            ),
                            'price': openapi.Schema(type=openapi.TYPE_INTEGER, description="Актуальная цена препарата", minimum=0),
                            'old_price': openapi.Schema(type=openapi.TYPE_INTEGER, description="Старая цена препарата (если была)", minimum=0, nullable=True),
                            'category': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории (например, Голова или Нога)"),
                            'tags': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                                description="Список ID тегов (например: антибиотик, противовоспалительное средство)",
                                nullable=True
                            ),
                            'links': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                                description="Ссылки на фотографии медицинского препарата",
                                nullable=True
                            ),
                            'total': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество единиц препарата в наличии", minimum=0),
                            'new': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Препарат является новым (True/False)", nullable=True),
                        }
                    ),
                    description="Список медицинских препаратов, связанных с этим тегом"
                )
            }
        )}
    )
    def retrieve(self, request, *args, **kwargs):
        tag = self.get_object()

        products = tag.products.all()
        product_data = []
        for product in products:
            product_data.append({
                'id': product.id,
                'title': product.title,
                'description_uz': product.description_uz,
                'description_ru': product.description_ru,
                'description_en': product.description_en,
                'instruction_uz': product.instruction_uz,
                'instruction_ru': product.instruction_ru,
                'instruction_en': product.instruction_en,
                'illness_uz': product.illness_uz,
                'illness_ru': product.illness_ru,
                'illness_en': product.illness_en,
                'composition_uz': product.composition_uz,
                'composition_ru': product.composition_ru,
                'composition_en': product.composition_en,
                'price': product.price,
                'old_price': product.old_price,
                'category': product.category.id if product.category else None,
                'tags': [tag.id for tag in product.tags.all()],
                'links': product.links,
                'total': product.total,
                'new': product.new,
            })

        return Response({
            'id': tag.id,
            'name_uz': tag.name_uz,
            'name_ru': tag.name_ru,
            'name_en': tag.name_en,
            'products': product_data
        })

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializers

    @swagger_auto_schema(
        operation_summary="Получить список категорий",
        operation_description="Возвращает список всех категорий, представляющих части тела или органы (например, Голова, Нога, Сердце), с их названиями на трёх языках (узбекский, русский, английский). Включает вложенные категории через поле 'children'.",
        responses={
            200: openapi.Response(
                description="Список категорий",
                schema=CategorySerializers(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные категории",
        operation_description="Возвращает данные конкретной категории, представляющей часть тела или орган (например, Голова), по её ID, включая названия на трёх языках и вложенные категории.",
        responses={
            200: openapi.Response(
                description="Данные категории",
                schema=CategorySerializers()
            ),
            404: "Категория не найдена"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новую категорию",
        operation_description="Создаёт новую категорию, представляющую часть тела или орган, с названиями на трёх языках. Поле 'parent' может быть указано для создания вложенной категории.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name_uz", "name_ru", "name_en"],
            properties={
                "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке (например, 'Bosh' для головы)"),
                "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке (например, 'Голова')"),
                "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке (например, 'Head')"),
                "parent": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID родительской категории (если есть)", nullable=True),
                "image": openapi.Schema(type=openapi.TYPE_STRING, format="binary", description="Изображение категории (если есть)", nullable=True),
            },
            example={
                "name_uz": "Oyoq",
                "name_ru": "Нога",
                "name_en": "Leg",
                "parent": None,
                "image": None
            }
        ),
        responses={
            201: openapi.Response(
                description="Категория успешно создана",
                schema=CategorySerializers()
            ),
            400: "Ошибка в данных запроса"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить данные категории (полное обновление)",
        operation_description="Обновляет данные указанной категории, представляющей часть тела или орган, по её ID. Все поля должны быть предоставлены.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name_uz", "name_ru", "name_en"],
            properties={
                "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке (например, 'Yurak' для сердца)"),
                "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке (например, 'Сердце')"),
                "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке (например, 'Heart')"),
                "parent": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID родительской категории (если есть)", nullable=True),
                "image": openapi.Schema(type=openapi.TYPE_STRING, format="binary", description="Изображение категории (если есть)", nullable=True),
            },
            example={
                "name_uz": "Yurak",
                "name_ru": "Сердце",
                "name_en": "Heart",
                "parent": None,
                "image": None
            }
        ),
        responses={
            200: openapi.Response(
                description="Категория успешно обновлена",
                schema=CategorySerializers()
            ),
            400: "Ошибка в данных запроса",
            404: "Категория не найдена"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные категории",
        operation_description="Частично обновляет данные указанной категории, представляющей часть тела или орган, по её ID. Можно обновить только указанные поля.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name_uz": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на узбекском языке", nullable=True),
                "name_ru": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на русском языке", nullable=True),
                "name_en": openapi.Schema(type=openapi.TYPE_STRING, description="Название категории на английском языке", nullable=True),
                "parent": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID родительской категории (если есть)", nullable=True),
                "image": openapi.Schema(type=openapi.TYPE_STRING, format="binary", description="Изображение категории (если есть)", nullable=True),
            },
            example={
                "name_ru": "Обновлённое сердце"
            }
        ),
        responses={
            200: openapi.Response(
                description="Категория успешно обновлена",
                schema=CategorySerializers()
            ),
            400: "Ошибка в данных запроса",
            404: "Категория не найдена"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить категорию",
        operation_description="Удаляет категорию, представляющую часть тела или орган, по её ID. Вложенные категории также могут быть затронуты в зависимости от настроек модели.",
        responses={
            204: openapi.Response(description="Категория успешно удалена"),
            404: "Категория не найдена"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers
    filter_backends = [CustomSearchFilter, DjangoFilterBackend]
    filterset_class = ProductFilter
    search_fields = [
        'title',
        'description_uz',
        'description_ru',
        'description_en',
        'instruction_uz',
        'instruction_ru',
        'instruction_en',
        'illness_uz',
        'illness_ru',
        'illness_en',
        'composition_uz',
        'composition_ru',
        'composition_en',
    ]

    def get_queryset(self):
        base_queryset = Product.objects.annotate(
            average_rating=Avg('comments__rating')
        )
        return self.get_filtered_queryset(base_queryset)

    def get_filtered_queryset(self, base_queryset):
        params = self.request.query_params.copy()

        tags = params.get('tags')
        if tags and ',' in tags:
            params.setlist('tags', tags.split(','))

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

        new_product = params.get('new')
        if new_product is not None:
            if new_product.lower() == 'true':
                base_queryset = base_queryset.filter(new=True)
            elif new_product.lower() == 'false':
                base_queryset = base_queryset.filter(new=False)

        filterset = self.filterset_class(params, queryset=base_queryset)
        if not filterset.is_valid():
            return base_queryset
        return filterset.qs

    @swagger_auto_schema(
        operation_summary="Получить список медицинских препаратов",
        operation_description="Возвращает список медицинских препаратов с возможностью фильтрации по цене, наличию старой цены, среднему рейтингу, возрастному диапазону, тегам (по ID или имени на любом языке) и поиску по названию или описанию. Препараты связаны с категориями, представляющими части тела или органы (например, Голова, Нога).",
        manual_parameters=[
            openapi.Parameter('has_old_price', openapi.IN_QUERY,
                              description="Фильтр по наличию старой цены (true/false)", type=openapi.TYPE_STRING),
            openapi.Parameter('new', openapi.IN_QUERY, description="Фильтр по статусу нового продукта (true/false)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('price_min', openapi.IN_QUERY, description="Минимальная цена", type=openapi.TYPE_INTEGER),
            openapi.Parameter('price_max', openapi.IN_QUERY, description="Максимальная цена",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('average_rating', openapi.IN_QUERY, description="Минимальный средний рейтинг",
                              type=openapi.TYPE_NUMBER),
            openapi.Parameter('age_range', openapi.IN_QUERY,
                              description="Возрастной диапазон (0-2, 3-7, 8-12, 13-17, 18+)", type=openapi.TYPE_STRING),
            openapi.Parameter('tags', openapi.IN_QUERY, description="ID тегов (например: 1) если нужны препараты с несколькими тегами: (tags=2&tags=1)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('tag_name', openapi.IN_QUERY,
                              description="Имя тега на любом языке (например: 'Антибиотик', 'Antibiotic', 'Antibiotik')",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY,
                              description="Поиск по названию, описанию, инструкции или составу",
                              type=openapi.TYPE_STRING),
        ],
        responses={200: ProductSerializers(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные медицинского препарата",
        operation_description="Возвращает данные конкретного медицинского препарата по его ID, включая название, описание, инструкции на трёх языках, цену, возрастной диапазон, средний рейтинг и ссылки на фотографии препарата. Препарат связан с категорией, представляющей часть тела или орган.",
        responses={200: ProductSerializers()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новый медицинский препарат",
        operation_description="Создание медицинского препарата с описанием на нескольких языках, инструкцией по применению, составом, ценой, тегами (например: 'Антибиотик', 'Обезболивающее'), возрастным диапазоном и ссылками на фотографии препарата. Препарат связывается с категорией, представляющей часть тела или орган (например, Голова).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "title", "description_uz", "description_ru", "description_en",
                "instruction_uz", "instruction_ru", "instruction_en",
                "price", "category", "total"
            ],
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название медицинского препарата",
                                        maxLength=100),
                "description_uz": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на узбекском языке"),
                "description_ru": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на русском языке"),
                "description_en": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на английском языке"),
                "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на узбекском языке"),
                "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на русском языке"),
                "instruction_en": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на английском языке"),
                "illness_uz": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (узбекский)",
                    nullable=True
                ),
                "illness_ru": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (русский)",
                    nullable=True
                ),
                "illness_en": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (английский)",
                    nullable=True
                ),
                "composition_uz": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (узбекский)",
                    nullable=True
                ),
                "composition_ru": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (русский)",
                    nullable=True
                ),
                "composition_en": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (английский)",
                    nullable=True
                ),
                "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Актуальная цена препарата", minimum=0),
                "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Старая цена препарата (если была)",
                                            minimum=0, nullable=True),
                "category": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории, представляющей часть тела или орган (например, Голова)"),
                "tags_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Список ID тегов (например: антибиотик, противовоспалительное средство)",
                    nullable=True
                ),
                "links": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                    description="Ссылки на фотографии медицинского препарата",
                    nullable=True
                ),
                "total": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество единиц препарата в наличии",
                                        minimum=0),
                "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Препарат является новым (True/False)",
                                      nullable=True),
                "age_range": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Возрастной диапазон (0-2, 3-7, 8-12, 13-17, 18+)",
                    enum=['0-2', '3-7', '8-12', '13-17', '18+'],
                    default='18+'
                ),
            },
            example={
                "title": "Анальгин Форте",
                "description_uz": "Bosh og'rig'ini kamaytirish uchun preparat",
                "description_ru": "Препарат для снятия головной боли",
                "description_en": "Headache relief medication",
                "instruction_uz": "Har kuni 1-2 tabletka ovqatdan keyin ichiladi.",
                "instruction_ru": "Принимать по 1-2 таблетки в день после еды.",
                "instruction_en": "Take 1-2 tablets daily after meals.",
                "illness_uz": ["bosh og'rig'i", "migren"],
                "illness_ru": ["головная боль", "мигрень"],
                "illness_en": ["headache", "migraine"],
                "composition_uz": ["metamizol natriy-500mg", "kofein-50mg"],
                "composition_ru": ["метамизол натрия-500мг", "кофеин-50мг"],
                "composition_en": ["metamizole sodium-500mg", "caffeine-50mg"],
                "price": 25000,
                "old_price": 30000,
                "category": 2,
                "tags_ids": [3],
                "links": ["https://pharmstd.ru/upload/300spravo4nik_lekarstva/form_181.jpg", "https://aptekonline.az//storage/ProductImages/5195_1.jpg"],
                "total": 150,
                "new": True,
                "age_range": "13-17"
            }
        ),
        responses={
            201: ProductSerializers,
            400: openapi.Response(description="Ошибка валидации данных"),
            401: openapi.Response(description="Ошибка авторизации"),
            404: openapi.Response(description="Категория или тег не найдены")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить данные медицинского препарата (полное обновление)",
        operation_description="Обновляет данные указанного медицинского препарата по его ID, включая ссылки на фотографии препарата. Препарат связывается с категорией, представляющей часть тела или орган.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "title", "description_uz", "description_ru", "description_en",
                "instruction_uz", "instruction_ru", "instruction_en",
                "price", "category", "total"
            ],
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название медицинского препарата",
                                        maxLength=100),
                "description_uz": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на узбекском языке"),
                "description_ru": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на русском языке"),
                "description_en": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на английском языке"),
                "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на узбекском языке"),
                "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на русском языке"),
                "instruction_en": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на английском языке"),
                "illness_uz": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (узбекский)",
                    nullable=True
                ),
                "illness_ru": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (русский)",
                    nullable=True
                ),
                "illness_en": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (английский)",
                    nullable=True
                ),
                "composition_uz": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (узбекский)",
                    nullable=True
                ),
                "composition_ru": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (русский)",
                    nullable=True
                ),
                "composition_en": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (английский)",
                    nullable=True
                ),
                "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Актуальная цена препарата", minimum=0),
                "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Старая цена препарата (если была)",
                                            minimum=0, nullable=True),
                "category": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории, представляющей часть тела или орган (например, Голова)"),
                "tags_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Список ID тегов (например: антибиотик, противовоспалительное средство)",
                    nullable=True
                ),
                "links": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                    description="Ссылки на фотографии медицинского препарата",
                    nullable=True
                ),
                "total": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество единиц препарата в наличии",
                                        minimum=0),
                "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Препарат является новым (True/False)",
                                      nullable=True),
                "age_range": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Возрастной диапазон (0-2, 3-7, 8-12, 13-17, 18+)",
                    enum=['0-2', '3-7', '8-12', '13-17', '18+'],
                    default='18+'
                ),
            },
            example={
                "title": "Анальгин Форте",
                "description_uz": "Bosh og'rig'ini kamaytirish uchun preparat",
                "description_ru": "Препарат для снятия головной боли",
                "description_en": "Headache relief medication",
                "instruction_uz": "Har kuni 1-2 tabletka ovqatdan keyin ichiladi.",
                "instruction_ru": "Принимать по 1-2 таблетки в день после еды.",
                "instruction_en": "Take 1-2 tablets daily after meals.",
                "illness_uz": ["bosh og'rig'i", "migren"],
                "illness_ru": ["головная боль", "мигрень"],
                "illness_en": ["headache", "migraine"],
                "composition_uz": ["metamizol natriy-500mg", "kofein-50mg"],
                "composition_ru": ["метамизол натрия-500мг", "кофеин-50мг"],
                "composition_en": ["metamizole sodium-500mg", "caffeine-50mg"],
                "price": 25000,
                "old_price": 30000,
                "category": 2,
                "tags_ids": [3],
                "links": ["https://pharmstd.ru/upload/300spravo4nik_lekarstva/form_181.jpg", "https://aptekonline.az//storage/ProductImages/5195_1.jpg"],
                "total": 150,
                "new": True,
                "age_range": "13-17"
            }
        ),
        responses={
            201: ProductSerializers,
            400: openapi.Response(description="Ошибка валидации данных"),
            401: openapi.Response(description="Ошибка авторизации"),
            404: openapi.Response(description="Категория или тег не найдены")
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные медицинского препарата",
        operation_description="Частично обновляет данные указанного медицинского препарата по его ID, включая ссылки на фотографии препарата. Препарат связывается с категорией, представляющей часть тела или орган.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название медицинского препарата",
                                        maxLength=100),
                "description_uz": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на узбекском языке"),
                "description_ru": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на русском языке"),
                "description_en": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Описание препарата на английском языке"),
                "instruction_uz": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на узбекском языке"),
                "instruction_ru": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на русском языке"),
                "instruction_en": openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Инструкция по применению на английском языке"),
                "illness_uz": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (узбекский)",
                    nullable=True
                ),
                "illness_ru": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (русский)",
                    nullable=True
                ),
                "illness_en": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Перечень заболеваний для лечения (английский)",
                    nullable=True
                ),
                "composition_uz": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (узбекский)",
                    nullable=True
                ),
                "composition_ru": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (русский)",
                    nullable=True
                ),
                "composition_en": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Состав препарата (английский)",
                    nullable=True
                ),
                "price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Актуальная цена препарата", minimum=0),
                "old_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Старая цена препарата (если была)",
                                            minimum=0, nullable=True),
                "category": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории, представляющей часть тела или орган (например, Голова)"),
                "tags_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Список ID тегов (например: антибиотик, противовоспалительное средство)",
                    nullable=True
                ),
                "links": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                    description="Ссылки на фотографии медицинского препарата",
                    nullable=True
                ),
                "total": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество единиц препарата в наличии",
                                        minimum=0),
                "new": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Препарат является новым (True/False)",
                                      nullable=True),
                "age_range": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Возрастной диапазон (0-2, 3-7, 8-12, 13-17, 18+)",
                    enum=['0-2', '3-7', '8-12', '13-17', '18+'],
                    default='18+'
                ),
            },
            example={
                "links": ["https://pharmstd.ru/upload/300spravo4nik_lekarstva/form_181.jpg", "https://aptekonline.az//storage/ProductImages/5195_1.jpg"],
            }
        ),
        responses={200: ProductSerializers()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить медицинский препарат",
        operation_description="Удаляет медицинский препарат по его ID.",
        responses={204: "Нет содержимого"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить препараты по категории",
        operation_description="Возвращает список медицинских препаратов в указанной категории, представляющей часть тела или орган (например, Голова), с возможностью фильтрации по цене, наличию старой цены и среднему рейтингу.",
        manual_parameters=[
            openapi.Parameter('category_id', openapi.IN_PATH, description="ID категории (например, Голова или Нога)", type=openapi.TYPE_INTEGER),
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        if product_id:
            return Comment.objects.filter(product_id=product_id).select_related('user', 'product')
        return Comment.objects.all().select_related('user', 'product')

    @swagger_auto_schema(
        operation_summary="Получить список комментариев",
        operation_description="Возвращает список комментариев для указанного медицинского препарата.",
        responses={
            200: openapi.Response(
                description="Список комментариев",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID комментария'),
                            'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария'),
                            'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)'),
                            'user': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID пользователя'),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Электронная почта'),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                                    'surname': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия пользователя'),
                                    'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер телефона'),
                                    'avatar': openapi.Schema(type=openapi.TYPE_STRING, format='uri', description='URL аватара'),
                                },
                                description='Информация о пользователе'
                            ),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата создания'),
                        }
                    )
                )
            ),
            404: "Продукт не найден"
        }
    )
    def list(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        if product_id and not Product.objects.filter(id=product_id).exists():
            raise ValidationError(f"Продукт с ID {product_id} не существует.")
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные комментария",
        operation_description="Возвращает данные конкретного комментария по его ID для указанного медицинского препарата.",
        responses={
            200: openapi.Response(
                description="Детали комментария",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID комментария'),
                        'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария'),
                        'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID пользователя'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Электронная почта'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                                'surname': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия пользователя'),
                                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер телефона'),
                                'avatar': openapi.Schema(type=openapi.TYPE_STRING, format='uri', description='URL аватара'),
                            }
                        ),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата создания'),
                    }
                )
            ),
            404: "Комментарий или продукт не найден"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        if product_id and not Product.objects.filter(id=product_id).exists():
            raise ValidationError(f"Продукт с ID {product_id} не существует.")
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новый комментарий",
        operation_description="Создаёт новый комментарий для медицинского препарата, указанного в URL (product_id). Пользователь должен быть аутентифицирован.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['text', 'rating'],
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария'),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)'),
            },
            example={
                'text': 'Отличный препарат для лечения головной боли!',
                'rating': 5.0
            }
        ),
        responses={
            201: openapi.Response(
                description="Комментарий успешно создан",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID комментария'),
                        'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария'),
                        'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID пользователя'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Электронная почта'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                                'surname': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия пользователя'),
                                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер телефона'),
                                'avatar': openapi.Schema(type=openapi.TYPE_STRING, format='uri', description='URL аватара'),
                            }
                        ),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата создания'),
                    }
                )
            ),
            400: "Неверные данные или неверный рейтинг",
            401: "Требуется аутентификация",
            404: "Продукт не найден"
        }
    )
    def create(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        if not product_id:
            raise ValidationError("Не указан product_id в URL.")
        try:
            Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValidationError(f"Продукт с ID {product_id} не существует.")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        serializer.save(product=product, user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Обновить комментарий (полное обновление)",
        operation_description="Обновляет текст и/или рейтинг указанного комментария для медицинского препарата. Только автор комментария может обновлять.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['text', 'rating'],
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария'),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)'),
            },
            example={
                'text': 'Обновленный комментарий о препарате',
                'rating': 4.0
            }
        ),
        responses={
            200: openapi.Response(
                description="Комментарий успешно обновлен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID комментария'),
                        'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария'),
                        'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID пользователя'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Электронная почта'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                                'surname': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия пользователя'),
                                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер телефона'),
                                'avatar': openapi.Schema(type=openapi.TYPE_STRING, format='uri', description='URL аватара'),
                            }
                        ),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата создания'),
                    }
                )
            ),
            400: "Неверные данные или неверный рейтинг",
            401: "Требуется аутентификация",
            403: "Недостаточно прав (не автор комментария)",
            404: "Комментарий или продукт не найден"
        }
    )
    def update(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        if product_id and not Product.objects.filter(id=product_id).exists():
            raise ValidationError(f"Продукт с ID {product_id} не существует.")
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить комментарий",
        operation_description="Частично обновляет текст или рейтинг указанного комментария для медицинского препарата. Только автор комментария может обновлять.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария', nullable=True),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)', nullable=True),
            },
            example={
                'rating': 3.0
            }
        ),
        responses={
            200: openapi.Response(
                description="Комментарий успешно обновлен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID комментария'),
                        'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст комментария'),
                        'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг (от 1.0 до 5.0)'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID пользователя'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Электронная почта'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                                'surname': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия пользователя'),
                                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Номер телефона'),
                                'avatar': openapi.Schema(type=openapi.TYPE_STRING, format='uri', description='URL аватара'),
                            }
                        ),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата создания'),
                    }
                )
            ),
            400: "Неверные данные или неверный рейтинг",
            401: "Требуется аутентификация",
            403: "Недостаточно прав (не автор комментария)",
            404: "Комментарий или продукт не найден"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        if product_id and not Product.objects.filter(id=product_id).exists():
            raise ValidationError(f"Продукт с ID {product_id} не существует.")
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить комментарий",
        operation_description="Удаляет комментарий по его ID для медицинского препарата. Только автор комментария может удалять.",
        responses={
            204: "Комментарий успешно удален",
            401: "Требуется аутентификация",
            403: "Недостаточно прав (не автор комментария)",
            404: "Комментарий или продукт не найден"
        }
    )
    def destroy(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        if product_id and not Product.objects.filter(id=product_id).exists():
            raise ValidationError(f"Продукт с ID {product_id} не существует.")
        return super().destroy(request, *args, **kwargs)

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

    @swagger_auto_schema(
        operation_summary="Получить список FAQ",
        operation_description="Возвращает список всех часто задаваемых вопросов (FAQ) о медицинских препаратах и их применении для различных частей тела или органов.",
        responses={
            200: openapi.Response(
                description="Список FAQ",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                            'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                            'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                            'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                            'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                            'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                            'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
                        }
                    )
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить детали FAQ",
        operation_description="Возвращает подробную информацию о конкретном FAQ, связанном с медицинскими препаратами или их применением для частей тела или органов.",
        responses={
            200: openapi.Response(
                description="Детали FAQ",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                        'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                        'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                        'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                        'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                        'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                        'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
                    }
                )
            ),
            404: "FAQ не найден"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новый FAQ",
        operation_description="Создает новый часто задаваемый вопрос (FAQ), связанный с медицинскими препаратами или их применением для частей тела или органов.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['question_uz', 'answer_uz'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
            },
            example={
                'question_uz': "Bosh og'rig'i uchun qaysi preparatlar tavsiya etiladi?",
                'question_ru': "Какие препараты рекомендуются для лечения головной боли?",
                'question_en': "Which medications are recommended for headache relief?",
                'answer_uz': "Bosh og'rig'i uchun Analdim yoki Paratsetamol kabi preparatlar tavsiya etiladi.",
                'answer_ru': "Для лечения головной боли рекомендуются препараты, такие как Анальгин или Парацетамол.",
                'answer_en': "For headache relief, medications like Analgin or Paracetamol are recommended."
            }
        ),
        responses={
            201: openapi.Response(
                description="FAQ успешно создан",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                        'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                        'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                        'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                        'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                        'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                        'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
                    },
                )
            ),
            400: "Неверные данные"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить FAQ",
        operation_description="Обновляет существующий FAQ, связанный с медицинскими препаратами или их применением для частей тела или органов.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['question_uz', 'answer_uz'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
            },
            example={
                'question_uz': "Bosh og'rig'i uchun qaysi preparatlar tavsiya etiladi?",
                'question_ru': "Какие препараты рекомендуются для лечения головной боли?",
                'question_en': "Which medications are recommended for headache relief?",
                'answer_uz': "Bosh og'rig'i uchun Analdim yoki Paratsetamol kabi preparatlar tavsiya etiladi.",
                'answer_ru': "Для лечения головной боли рекомендуются препараты, такие как Анальгин или Парацетамол.",
                'answer_en': "For headache relief, medications like Analgin or Paracetamol are recommended."
            }
        ),
        responses={
            200: openapi.Response(
                description="FAQ успешно обновлен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                        'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                        'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                        'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                        'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                        'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                        'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
                    },
                )
            ),
            400: "Неверные данные",
            404: "FAQ не найден"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить FAQ",
        operation_description="Частично обновляет существующий FAQ, связанный с медицинскими препаратами или их применением для частей тела или органов.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
            },
            example={
                'answer_en': "For headache relief, medications like Analgin or Ibuprofen are recommended."
            }
        ),
        responses={
            200: openapi.Response(
                description="FAQ успешно обновлен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID FAQ'),
                        'question_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на узбекском'),
                        'question_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на русском'),
                        'question_en': openapi.Schema(type=openapi.TYPE_STRING, description='Вопрос на английском'),
                        'answer_uz': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на узбекском'),
                        'answer_ru': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на русском'),
                        'answer_en': openapi.Schema(type=openapi.TYPE_STRING, description='Ответ на английском'),
                    },
                )
            ),
            400: "Неверные данные",
            404: "FAQ не найден"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить FAQ",
        operation_description="Удаляет существующий FAQ, связанный с медицинскими препаратами или их применением.",
        responses={
            204: "FAQ успешно удален",
            404: "FAQ не найден"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)