# Generated by Django 5.0.1 on 2024-01-31 15:22

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Zacapp', '0004_alter_orderupdate_update_desc'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='order_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
