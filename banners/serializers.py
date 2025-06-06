from rest_framework import serializers
from .models import Banner

class BannerSerializer(serializers.ModelSerializer):

    class Meta:
        model=Banner
        fields=['id', 'image', 'title_uz', 'title_ru', 'title_en', 'description_uz', 'description_ru', 'description_en']