# Generated by Django 3.2.2 on 2021-05-08 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0002_auto_20210508_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='hasgpu',
            field=models.BooleanField(default=False),
        ),
    ]