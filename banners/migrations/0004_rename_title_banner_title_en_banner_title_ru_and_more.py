# Generated by Django 5.1.7 on 2025-04-23 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banners', '0003_rename_description_banner_description_en_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='banner',
            old_name='title',
            new_name='title_en',
        ),
        migrations.AddField(
            model_name='banner',
            name='title_ru',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='banner',
            name='title_uz',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
