from django.contrib import admin
from .models import Order

class ProductInline(admin.TabularInline):
    model = Order.products.through
    extra = 0
    readonly_fields = ('product',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'status', 'get_total_price')

    list_filter = ('status',)

    search_fields = ('user__email',)

    list_per_page = 20

    inlines = [ProductInline]

    def get_total_price(self, obj):
        return sum(product.price for product in obj.products.all())
    get_total_price.short_description = 'Общая сумма'
