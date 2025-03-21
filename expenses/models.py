# expenses/models.py

from decimal import Decimal
import uuid
from django.db import models
from Template.models import UppercaseCharField
from users.models import User
from common.models import Airline, ExchangeRate, RentalAgency, CarType, MealCategory, RelationshipToPAI, City, HotelDailyBaseRate, MileageRate

class ExpenseReport(models.Model):
    class ReportStatus(models.TextChoices):
        OPEN = "Open", "Open"
        SUBMITTED = "Submitted", "Submitted"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"
        PAID = "Paid", "Paid"

    class IntegrationStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        SUCCESS = "Success", "Success"
        FAILURE = "Failure", "Failure"

    id = models.AutoField(primary_key=True)
    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    report_number = models.CharField(max_length=20)
    report_status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.OPEN)
    report_date = models.DateField(null=True)
    expense_type = models.CharField(max_length=100)
    purpose = models.CharField(max_length=1000)
    payment_method = models.CharField(max_length=100)
    report_amount = models.DecimalField(max_digits=10, decimal_places=2)
    report_currency = UppercaseCharField(max_length=5)
    report_submit_date = models.DateField(null=True)
    integration_status = models.CharField(max_length=10, choices=IntegrationStatus.choices, default=IntegrationStatus.PENDING)
    integration_date = models.DateField(null=True)
    error = models.BooleanField(default=True)
    iexp_report_status = models.CharField(max_length=100, null=True, blank=True)
    iexp_report_number = models.CharField(max_length=100, null=True, blank=True)
    paid_amount = models.CharField(max_length=100, null=True, blank=True)
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
        if self.report_currency:
            self.report_currency = self.report_currency.upper()
        
        request = kwargs.pop("request", None)

        if not self.pk and request and hasattr(request, "user"):
            self.created_by = request.user

        if self.pk and request and hasattr(request, "user"):
            self.updated_by = request.user

        super().save(*args, **kwargs)

class ExpenseItem(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    report = models.ForeignKey(ExpenseReport, null=True, on_delete=models.CASCADE)
    expense_type = models.CharField(max_length=50)
    expense_date = models.DateField(null=True)
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=6, null=True)
    payment_method = models.CharField(max_length=100, default="Cash")
    receipt_amount = models.CharField(max_length=200)
    receipt_currency = UppercaseCharField(max_length=5)
    justification = models.CharField(max_length=2000)
    note = models.CharField(max_length=2000, null=True)

    airline = models.ForeignKey(Airline, null=True, on_delete=models.SET_NULL)
    origin_destination = models.CharField(max_length=200, null=True)
    rental_agency = models.ForeignKey(RentalAgency, null=True, on_delete=models.SET_NULL)
    car_type = models.ForeignKey(CarType, null=True, on_delete=models.SET_NULL)
    meal_category = models.ForeignKey(MealCategory, null=True, on_delete=models.SET_NULL)
    employee_names = models.CharField(max_length=2000, null=True)
    total_employees = models.IntegerField(null=True)
    employee_names2 = models.CharField(max_length=200, null=True, blank=True, default="N/A")
    company_customer_name_title = models.CharField(max_length=2000, null=True)
    business_topic = models.CharField(max_length=200, null=True)
    total_attendees = models.IntegerField(null=True)
    attendee1 = models.CharField(max_length=200, null=True, default="N/A")
    attendee2 = models.CharField(max_length=200, null=True, default="N/A")
    attendee3 = models.CharField(max_length=200, null=True, default="N/A")
    attendee4 = models.CharField(max_length=200, null=True, default="N/A")
    attendee5 = models.CharField(max_length=200, null=True, default="N/A")
    attendee6 = models.CharField(max_length=200, null=True, default="N/A")
    attendee7 = models.CharField(max_length=200, null=True, default="N/A")
    attendee8 = models.CharField(max_length=200, null=True, default="N/A")
    attendee9 = models.CharField(max_length=200, null=True, default="N/A")
    attendee10 = models.CharField(max_length=200, null=True, default="N/A")
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
        
    def save(self, *args, **kwargs):
        if self.receipt_currency:
            self.receipt_currency = self.receipt_currency.upper()
        
        request = kwargs.pop("request", None)

        user = getattr(request, "user", None) if request else None
        user_default_currency = getattr(user, "currency", None) if user else None
        if user_default_currency:
            user_default_currency = user_default_currency.upper()

        if self.receipt_currency and user_default_currency and self.receipt_currency != user_default_currency:
            self.exchange_rate = self.get_exchange_rate(self.receipt_currency, user_default_currency)

        if not self.pk and request and hasattr(request, "user"):
            self.created_by = request.user

        if self.pk and request and hasattr(request, "user"):
            self.updated_by = request.user

        super().save(*args, **kwargs)

    def get_exchange_rate(self, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal(1)
        try:
            latest_rate = ExchangeRate.objects.latest('date_fetched')
            from_rate = ExchangeRate.objects.get(target_currency=from_currency, date_fetched=latest_rate.date_fetched).rate
            to_rate = ExchangeRate.objects.get(target_currency=to_currency, date_fetched=latest_rate.date_fetched).rate
            return to_rate / from_rate
        except ExchangeRate.DoesNotExist:
            return None
        

class ExpenseReceipt(models.Model):
    id = models.AutoField(primary_key=True)
    expense_item = models.ForeignKey(ExpenseItem, related_name="receipts", on_delete=models.CASCADE)
    s3_path = models.CharField(max_length=2000, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'expense_receipt'

    def __str__(self):
        return f"Receipt {self.id} for ExpenseItem {self.expense_item.id} - {self.receipt_amount} {self.receipt_currency}"


