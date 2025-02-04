# common/models.py
from django.db import models
from django.utils import timezone

from Template.models import UppercaseCharField

class Airline(models.Model):
    value = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'airline'

    def __str__(self):
        return self.value

class RentalAgency(models.Model):
    value = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'rental_agency'

    def __str__(self):
        return self.value

class CarType(models.Model):
    value = models.CharField(max_length=200)
    description = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'car_type'

    def __str__(self):
        return self.value

class MealCategory(models.Model):
    value = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'meal_category'

    def __str__(self):
        return self.value

class RelationshipToPAI(models.Model):
    value = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'relationship_to_pai'

    def __str__(self):
        return self.value

class City(models.Model):
    value = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'city'

    def __str__(self):
        return self.value

class HotelDailyBaseRate(models.Model):
    country = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = UppercaseCharField(max_length=5)

    class Meta:
        db_table = 'hotel_daily_base_rate'

    def __str__(self):
        return f'{self.country} {self.city} {self.amount} {self.currency}'

class MileageRate(models.Model):
    rate = models.DecimalField(max_digits=3, decimal_places=2, unique=True)
    title = models.CharField(max_length=3)

    class Meta:
        db_table = 'mileage_rate'

    def __str__(self):
        return f'{self.rate} {self.title}'
    
class ExchangeRate(models.Model):
    target_currency = UppercaseCharField(max_length=5)
    rate = models.DecimalField(max_digits=20, decimal_places=6)
    date_fetched = models.DateTimeField(default=timezone.now)
    next_update_time = models.DateTimeField()
    
    class Meta:
        db_table = 'exchange_rate'