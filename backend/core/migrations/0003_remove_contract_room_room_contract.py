# Generated by Django 4.2 on 2023-04-27 18:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_room_window'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contract',
            name='room',
        ),
        migrations.AddField(
            model_name='room',
            name='contract',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room', to='core.contract'),
        ),
    ]
