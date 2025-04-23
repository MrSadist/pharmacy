from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'avatar')
    search_fields = ('name', 'surname')
