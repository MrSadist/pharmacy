# Generated by Django 5.1.7 on 2025-05-07 18:34

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='chat',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='message',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name='chat',
            constraint=models.UniqueConstraint(fields=('user', 'specialist'), name='unique_user_specialist_chat'),
        ),
    ]
