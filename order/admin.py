from django import forms
from django.contrib import admin
from products.models import Product
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'get_item_total')
    readonly_fields = ('get_item_total',)

    def get_item_total(self, obj):
        return obj.product.price * obj.quantity
    get_item_total.short_description = 'Стоимость'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'product':
            kwargs['queryset'] = Product.objects.filter(total__gt=0)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def clean(self):
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                product = form.cleaned_data.get('product')
                quantity = form.cleaned_data.get('quantity')
                if product and quantity and product.total < quantity:
                    raise forms.ValidationError(
                        f"Недостаточно товара для продукта {product.title}: "
                        f"доступно {product.total}, запрошено {quantity}."
                    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user_full_name', 'created_at', 'status', 'address', 'comment', 'get_total_items', 'get_total_price')
    list_filter = ('status', 'user')
    search_fields = ('user__email', 'user__name', 'user__surname', 'address', 'comment')
    list_per_page = 20
    list_editable = ('status', 'address', 'comment')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'created_at')
        }),
        ('Дополнительная информация', {
            'fields': ('address', 'comment')
        }),
    )
    actions = ['mark_as_pending', 'mark_as_shipping', 'mark_as_delivered', 'mark_as_cancelled']

    def get_user_full_name(self, obj):
        return f"{obj.user.name} {obj.user.surname}"
    get_user_full_name.short_description = 'Клиент'

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())
    get_total_items.short_description = 'Количество продуктов'

    def get_total_price(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())
    get_total_price.short_description = 'Общая сумма'

    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
    mark_as_pending.short_description = 'Пометить как ожидает'

    def mark_as_shipping(self, request, queryset):
        queryset.update(status='shipping')
    mark_as_shipping.short_description = 'Пометить как отправлен'

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = 'Пометить как доставлен'

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_as_cancelled.short_description = 'Пометить как отменен'