# Generated by Django 4.2 on 2023-05-24 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_alter_suggestedcontract_contract'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='inquiry',
            options={'ordering': ['read', '-created_at']},
        ),
        migrations.AddField(
            model_name='inquiry',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]