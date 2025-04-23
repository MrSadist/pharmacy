from django.contrib import admin
from .models import Banner

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title_en',)
    search_fields = ('title_uz', 'title_ru', 'title_en','description_uz', 'description_ru', 'description_en')
