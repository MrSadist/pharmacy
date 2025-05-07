from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'name', 'surname', 'role', 'phone_number', 'is_staff', 'is_active')

    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

    search_fields = ('email', 'name', 'surname', 'phone_number')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('name', 'surname', 'phone_number', 'avatar')}),
        ('Роли и права', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Избранное', {'fields': ('favorites',)}),
        ('OTP', {'fields': ('otp_code', 'otp_created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
            'email', 'name', 'surname', 'phone_number', 'password1', 'password2', 'role', 'is_staff', 'is_active'),
        }),
    )

    readonly_fields = ('otp_created_at',)

    ordering = ('email',)

    filter_horizontal = ('favorites',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related().prefetch_related('favorites')


admin.site.register(CustomUser, CustomUserAdmin)
