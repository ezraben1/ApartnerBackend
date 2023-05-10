# Generated by Django 4.2 on 2023-05-07 18:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_alter_contract_owner_alter_room_apartment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apartment',
            name='owner',
            field=models.ForeignKey(default=None, help_text='The user that owns the apartment.', on_delete=django.db.models.deletion.CASCADE, related_name='apartments_owned', to=settings.AUTH_USER_MODEL),
        ),
    ]