# Generated by Django 4.2 on 2023-05-24 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_remove_contract_price_suggested_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suggestedcontract',
            name='contract',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suggestions', to='core.contract'),
        ),
    ]
