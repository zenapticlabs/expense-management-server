# Generated by Django 5.0.7 on 2025-02-04 19:54

import Template.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='currency',
            field=Template.models.UppercaseCharField(default='USD', max_length=5),
        ),
    ]
