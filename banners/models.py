from django.db import models

class Banner(models.Model):
    image=models.ImageField(upload_to='banners')
    title_uz=models.CharField(max_length=100)
    title_ru=models.CharField(max_length=100)
    title_en=models.CharField(max_length=100)
    description_uz=models.TextField()
    description_ru=models.TextField()
    description_en=models.TextField()


    def __str__(self):
        return self.title_en