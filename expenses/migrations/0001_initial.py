# Generated by Django 4.2.4 on 2024-11-05 18:34

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseItem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('item_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('expense_type', models.CharField(max_length=50)),
                ('expense_date', models.DateField(null=True)),
                ('receipt_amount', models.CharField(max_length=200)),
                ('receipt_currency', models.CharField(max_length=200)),
                ('justification', models.CharField(max_length=2000)),
                ('note', models.CharField(max_length=2000, null=True)),
                ('s3_path', models.CharField(blank=True, max_length=255, null=True)),
                ('origin_destination', models.CharField(max_length=200, null=True)),
                ('employee_names', models.CharField(max_length=2000, null=True)),
                ('total_employees', models.IntegerField(null=True)),
                ('company_customer_name', models.CharField(max_length=2000, null=True)),
                ('business_topic', models.CharField(max_length=200, null=True)),
                ('total_attendees', models.IntegerField(null=True)),
                ('name_of_establishment', models.CharField(max_length=200, null=True)),
                ('hotel_name', models.CharField(max_length=200, null=True)),
                ('carrier', models.CharField(max_length=200, null=True)),
                ('distance', models.CharField(max_length=200, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'expense_item',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ExpenseReport',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('report_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('report_number', models.CharField(max_length=20)),
                ('report_status', models.CharField(max_length=100)),
                ('report_date', models.DateField(null=True)),
                ('expense_type', models.CharField(max_length=100)),
                ('purpose', models.CharField(max_length=1000)),
                ('payment_method', models.CharField(max_length=100)),
                ('report_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('report_currency', models.CharField(max_length=5)),
                ('report_submit_date', models.DateField(null=True)),
                ('integration_status', models.CharField(max_length=100)),
                ('integration_date', models.DateField(null=True)),
                ('error', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'expense_report',
                'managed': True,
            },
        ),
    ]
