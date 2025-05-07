from rest_framework.filters import SearchFilter
from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Product, Tag, AGE_RANGE_CHOICES


class CustomSearchFilter(SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_terms = request.query_params.get(self.search_param, None)
        if not search_terms:
            return queryset

        q_objects = Q()
        text_fields = [
            'title',
            'description_uz',
            'description_ru',
            'description_en',
            'instruction_uz',
            'instruction_ru',
            'instruction_en',
        ]
        for field in text_fields:
            q_objects |= Q(**{f'{field}__icontains': search_terms})

        json_fields = [
            'illness_uz',
            'illness_ru',
            'illness_en',
            'composition_uz',
            'composition_ru',
            'composition_en',
        ]

        filtered_ids = set()
        for obj in queryset:
            include = False
            for field in json_fields:
                json_data = getattr(obj, field) or []
                if isinstance(json_data, list):
                    text = ' '.join(str(item) for item in json_data)
                    if search_terms.lower() in text.lower():
                        include = True
                elif isinstance(json_data, str):
                    if search_terms.lower() in json_data.lower():
                        include = True
            if include:
                filtered_ids.add(obj.id)

        return queryset.filter(q_objects | Q(id__in=filtered_ids))


class ProductFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags',
        queryset=Tag.objects.all(),
        conjoined=True,
        to_field_name='id',
        method='filter_tags'
    )
    tag_name = filters.CharFilter(
        method='filter_by_tag_name',
        help_text="Фильтр по имени тега на любом языке (узбекском, русском, английском)"
    )
    age_range = filters.ChoiceFilter(
        choices=AGE_RANGE_CHOICES,
        help_text="Фильтр по возрастному диапазону (0-2, 3-7, 8-12, 13-17, 18+)"
    )

    def filter_tags(self, queryset, name, value):
        if value:
            for tag in value:
                queryset = queryset.filter(tags=tag)
        return queryset

    def filter_by_tag_name(self, queryset, name, value):

        return queryset.filter(
            Q(tags__name_uz__icontains=value) |
            Q(tags__name_ru__icontains=value) |
            Q(tags__name_en__icontains=value)
        ).distinct()

    class Meta:
        model = Product
        fields = ['tags', 'tag_name', 'age_range']
