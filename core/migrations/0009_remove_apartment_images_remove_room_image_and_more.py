# Generated by Django 4.2 on 2023-04-30 20:15

import core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_rename_image_apartment_images'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='apartment',
            name='images',
        ),
        migrations.RemoveField(
            model_name='room',
            name='image',
        ),
        migrations.AddField(
            model_name='apartmentimage',
            name='apartment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='core.apartment'),
        ),
        migrations.AddField(
            model_name='roomimage',
            name='room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='core.room'),
        ),
        migrations.AlterField(
            model_name='apartmentimage',
            name='image',
            field=models.ImageField(blank=True, help_text='The image of the apartment.', null=True, upload_to='apartment_images/', validators=[core.validators.validate_file_size]),
        ),
        migrations.AlterField(
            model_name='roomimage',
            name='image',
            field=models.ImageField(blank=True, help_text='The image of the room.', null=True, upload_to='room_images/', validators=[core.validators.validate_file_size]),
        ),
    ]