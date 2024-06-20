# common/serializers.py

from rest_framework import serializers
from .models import Airline, ExchangeRate, RentalAgency, CarType, MealCategory, RelationshipToPAI, City, HotelDailyBaseRate, MileageRate

class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ['value']

class RentalAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalAgency
        fields = ['value']

class CarTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarType
        fields = ['value', 'description']

class MealCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MealCategory
        fields = ['value']

class RelationshipToPAISerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationshipToPAI
        fields = ['value']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['value']

class HotelDailyBaseRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelDailyBaseRate
        fields = "__all__"

class MileageRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MileageRate
        fields = ['id', 'rate', 'title']
        
class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ['id', 'target_currency', 'rate', 'date_fetched']
