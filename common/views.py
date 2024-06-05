# common/views.py

from rest_framework import generics
from .models import Airline, RentalAgency, CarType, MealCategory, RelationshipToPAI, City, HotelDailyBaseRate, MileageRate
from .serializers import AirlineSerializer, RentalAgencySerializer, CarTypeSerializer, MealCategorySerializer, RelationshipToPAISerializer, CitySerializer, HotelDailyBaseRateSerializer, MileageRateSerializer

class AirlineListView(generics.ListAPIView):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer

class RentalAgencyListView(generics.ListAPIView):
    queryset = RentalAgency.objects.all()
    serializer_class = RentalAgencySerializer

class CarTypeListView(generics.ListAPIView):
    queryset = CarType.objects.all()
    serializer_class = CarTypeSerializer

class MealCategoryListView(generics.ListAPIView):
    queryset = MealCategory.objects.all()
    serializer_class = MealCategorySerializer

class RelationshipToPAIListView(generics.ListAPIView):
    queryset = RelationshipToPAI.objects.all()
    serializer_class = RelationshipToPAISerializer

class CityListView(generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class HotelDailyBaseRateListView(generics.ListAPIView):
    queryset = HotelDailyBaseRate.objects.all()
    serializer_class = HotelDailyBaseRateSerializer

class MileageRateListView(generics.ListAPIView):
    queryset = MileageRate.objects.all()
    serializer_class = MileageRateSerializer
