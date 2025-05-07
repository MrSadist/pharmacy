from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CommentViewSet, CategoryViewSet, TagViewSet, FAQViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products/(?P<product_id>\d+)/comments', CommentViewSet, basename='comment')
router.register(r'tags', TagViewSet)
router.register(r'FAQ', FAQViewSet)

urlpatterns = [
    path('', include(router.urls)),
]