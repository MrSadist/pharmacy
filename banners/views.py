from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Banner
from .serializers import BannerSerializer

class BannerListCreateView(APIView):
    @swagger_auto_schema(
        operation_summary="Получить список баннеров",
        operation_description="Возвращает все баннеры с заголовками и описаниями на 3 языках.",
        responses={200: BannerSerializer(many=True)}
    )
    def get(self, request):
        banners = Banner.objects.all()
        serializer = BannerSerializer(banners, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Создание нового баннера",
        operation_description="Создаёт баннер с полями: image, title (на 3 языках), description (на 3 языках).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["image", "title_uz", "description_uz"],
            properties={
                "image": openapi.Schema(type=openapi.TYPE_STRING, format="binary"),
                "title_uz": openapi.Schema(type=openapi.TYPE_STRING),
                "title_ru": openapi.Schema(type=openapi.TYPE_STRING),
                "title_en": openapi.Schema(type=openapi.TYPE_STRING),
                "description_uz": openapi.Schema(type=openapi.TYPE_STRING),
                "description_ru": openapi.Schema(type=openapi.TYPE_STRING),
                "description_en": openapi.Schema(type=openapi.TYPE_STRING),
            },
            example={
                "title_uz": "Aksiya",
                "title_ru": "Акция",
                "title_en": "Promo",
                "description_uz": "Yangilik bor",
                "description_ru": "Есть новость",
                "description_en": "There's a news"
            }
        ),
        responses={201: BannerSerializer()}
    )
    def post(self, request):
        serializer = BannerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BannerDetailView(APIView):
    @swagger_auto_schema(
        operation_summary="Получить один баннер",
        operation_description="Возвращает конкретный баннер по ID.",
        responses={200: BannerSerializer()}
    )
    def get(self, request, pk):
        banners = get_object_or_404(Banner, pk=pk)
        serializer = BannerSerializer(banners)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Обновить баннер",
        operation_description="Обновляет указанный баннер по ID.",
        request_body=BannerSerializer,
        responses={200: BannerSerializer()}
    )
    def put(self, request, pk):
        banners = get_object_or_404(Banner, pk=pk)
        serializer = BannerSerializer(banners, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Удалить баннер",
        operation_description="Удаляет баннер по ID.",
        responses={204: "No Content"}
    )
    def delete(self, request, pk):
        banners = get_object_or_404(Banner, pk=pk)
        banners.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)