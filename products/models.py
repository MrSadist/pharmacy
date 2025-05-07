from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
AGE_RANGE_CHOICES = [
    ('0-2', '0-2 years (Infants)'),
    ('3-7', '3-7 years (Young Children)'),
    ('8-12', '8-12 years (Children)'),
    ('13-17', '13-17 years (Teenagers)'),
    ('18+', '18+ years (Adults)'),
]

class Tag(models.Model):
    name_uz = models.CharField(max_length=100, db_index=True)
    name_ru = models.CharField(max_length=100, db_index=True)
    name_en = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name_en


class Category(models.Model):
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True)
    name_uz = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories', blank=True, null=True)

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
    illness_uz = models.JSONField(default=list, blank=True, null=True)
    illness_ru = models.JSONField(default=list, blank=True, null=True)
    illness_en = models.JSONField(default=list, blank=True, null=True)
    composition_uz = models.JSONField(default=list, blank=True, null=True)
    composition_ru = models.JSONField(default=list, blank=True, null=True)
    composition_en = models.JSONField(default=list, blank=True, null=True)
    price = models.PositiveIntegerField()
    old_price = models.PositiveIntegerField(blank=True,  null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    links = models.JSONField(default=list, blank=True, null=True)
    total = models.PositiveIntegerField()
    new = models.BooleanField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='products', blank=True)
    age_range = models.CharField(
        max_length=10,
        choices=AGE_RANGE_CHOICES,
        default='18+',
    )
    def __str__(self):
        return self.title

class Comment(models.Model):
    product = models.ForeignKey(Product, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    text = models.TextField()
    rating = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment for {self.product.title} ({self.rating})"


class FAQ(models.Model):
    question_uz = models.TextField()
    question_ru = models.TextField()
    question_en = models.TextField()
    answer_uz = models.TextField()
    answer_ru = models.TextField()
    answer_en = models.TextField()

    def __str__(self):
        return self.question