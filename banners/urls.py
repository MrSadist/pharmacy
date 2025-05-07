from django.urls import path
from .views import BannerDetailView, BannerListCreateView


urlpatterns = [
    path('banners/', BannerListCreateView.as_view(), name='banners_create'),
    path('banners/<int:pk>/', BannerDetailView.as_view(), name='banners_detail'),
]