# Generated by Django 4.2 on 2023-05-13 16:13

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_contract_file_url_alter_apartmentimage_image_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contract',
            name='file_url',
        ),
        migrations.AlterField(
            model_name='apartmentimage',
            name='image',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='bill',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='inquiry',
            name='image',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='roomimage',
            name='image',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='image'),
        ),
    ]
