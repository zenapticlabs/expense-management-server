# expenses/models.py

import uuid
from django.db import models
from users.models import User
from common.models import Airline, RentalAgency, CarType, MealCategory, RelationshipToPAI, City, HotelDailyBaseRate, MileageRate

class ExpenseReport(models.Model):
    id = models.AutoField(primary_key=True)
    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    report_number = models.CharField(max_length=20)
    report_status = models.CharField(max_length=100)
    report_date = models.DateField(null=True)
    expense_type = models.CharField(max_length=100)
    purpose = models.CharField(max_length=1000)
    payment_method = models.CharField(max_length=100)
    report_amount = models.DecimalField(max_digits=10, decimal_places=2)
    report_currency = models.CharField(max_length=5)
    report_submit_date = models.DateField(null=True)
    integration_status = models.CharField(max_length=100)
    integration_date = models.DateField(null=True)
    error = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'expense_report'
        
    def save(self, *args, **kwargs):
        if not self.report_number:
            last_report = ExpenseReport.objects.all().order_by('created_at').last()
            if last_report:
                last_report_number = int(last_report.report_number)
                self.report_number = f'{last_report_number + 1:04d}'
            else:
                self.report_number = '1000'
        super().save(*args, **kwargs)

class ExpenseItem(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    report = models.ForeignKey(ExpenseReport, null=True, on_delete=models.CASCADE)
    expense_type = models.CharField(max_length=50)
    expense_date = models.DateField(null=True)
    receipt_amount = models.CharField(max_length=200)
    receipt_currency = models.CharField(max_length=200)
    justification = models.CharField(max_length=2000)
    note = models.CharField(max_length=2000, null=True)
    s3_path = models.CharField(max_length=255, null=True, blank=True)

    airline = models.ForeignKey(Airline, null=True, on_delete=models.SET_NULL)
    origin_destination = models.CharField(max_length=200, null=True)
    rental_agency = models.ForeignKey(RentalAgency, null=True, on_delete=models.SET_NULL)
    car_type = models.ForeignKey(CarType, null=True, on_delete=models.SET_NULL)
    meal_category = models.ForeignKey(MealCategory, null=True, on_delete=models.SET_NULL)
    employee_names = models.CharField(max_length=2000, null=True)
    total_employees = models.IntegerField(null=True)
    company_customer_name = models.CharField(max_length=2000, null=True)
    business_topic = models.CharField(max_length=200, null=True)
    total_attendees = models.IntegerField(null=True)
    relationship_to_pai = models.ForeignKey(RelationshipToPAI, null=True, on_delete=models.SET_NULL)
    name_of_establishment = models.CharField(max_length=200, null=True)
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL)
    hotel_name = models.CharField(max_length=200, null=True)
    hotel_daily_base_rate = models.ForeignKey(HotelDailyBaseRate, null=True, on_delete=models.SET_NULL)
    carrier = models.CharField(max_length=200, null=True)
    distance = models.CharField(max_length=200, null=True)
    mileage_rate = models.ForeignKey(MileageRate, null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'expense_item'