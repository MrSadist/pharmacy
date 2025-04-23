from django.contrib import admin
from django import forms
from .models import Product, Comment, Category


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
class ProductAdminForm(forms.ModelForm):
    class Meta:
        model=Product
        fields = '__all__'
        widgets = {
            'link': forms.Textarea(attrs={'rows':5, 'cols':50, 'placeholder': 'enter links in JSON format, for example: \n["http://example.com", "http://anotherlink.com",]'})
        }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('title', 'price', 'total',)
    search_fields = ('title', 'description')
    inlines = [CommentInline]

    def links_display(self, obj):
        return ", ".join(obj.link) if obj.link else "No links"
    links_display.short_description = "links"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('product', 'text', 'rating', 'created_at')
    search_fields = ('text','product')

    fields = ('product', 'text', 'rating',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_en',)
    search_fields = ('name_en', 'name_ru', 'name_uz')
