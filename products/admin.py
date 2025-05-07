from django.contrib import admin
from django import forms
from .models import Product, Comment, Category, Tag, FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_en', 'answer_en')
    search_fields = ('question_en', 'question_uz', 'question_ru')


class CommentInline(admin.TabularInline):
    model = Comment
    fk_name = 'product'
    extra = 1
class ProductAdminForm(forms.ModelForm):
    class Meta:
        model=Product
        fields = '__all__'
        widgets = {
            'links': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'enter links in JSON format, for example: \n["http://example.com", "http://anotherlink.com",]'}),
            'illness_uz': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'enter illness in JSON format, for example: \n["bosh og`rig`iga", "tish og`rig`iga",]'}),
            'illness_ru': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'enter illness in JSON format, for example: \n["от головной боли", "от зубной боли",]'}),
            'illness_en': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'enter illness in JSON format, for example: \n["for headache", "for toothache",]'}),
            'composition_uz': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'enter composition in JSON format, for example: \n["krahmal-24,3mg", "povidon-10,2mg",]'}),
            'composition_ru': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'enter composition in JSON format, for example: \n["крахмал-24б3мг", "повидон-10,2мг",]'}),
            'composition_en': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'enter composition in JSON format, for example: \n["starch-24,3mg", "povidone-10,2mg",]'}),
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
    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_en',)
    search_fields = ('name_en', 'name_ru', 'name_uz')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name_en',)
    search_fields = ('name_en', 'name_ru', 'name_uz')

