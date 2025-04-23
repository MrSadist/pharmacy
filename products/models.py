from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Category(models.Model):
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True)
    name_uz = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)

    def __str__(self):
        return self.name_en

class Product(models.Model):
    title = models.CharField(max_length=100)
    description_uz = models.TextField()
    description_ru = models.TextField()
    description_en = models.TextField()
    instruction_uz = models.TextField()
    instruction_ru = models.TextField()
    instruction_en = models.TextField()
    price = models.PositiveIntegerField()
    old_price = models.PositiveIntegerField(blank=True,  null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    link = models.JSONField(default=list, blank=True, null=True)
    total = models.PositiveIntegerField()
    new = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    product = models.ForeignKey(Product, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment for {self.product.title} ({self.rating})"