# common/views.py
import requests
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Airline, ExchangeRate, RentalAgency, CarType, MealCategory, RelationshipToPAI, City, HotelDailyBaseRate, MileageRate
from .serializers import AirlineSerializer, ExchangeRateSerializer, RentalAgencySerializer, CarTypeSerializer, MealCategorySerializer, RelationshipToPAISerializer, CitySerializer, HotelDailyBaseRateSerializer, MileageRateSerializer
from django.utils import timezone

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
    
class ExchangeRateListView(generics.ListAPIView):
    serializer_class = ExchangeRateSerializer

    def get_queryset(self):
        return ExchangeRate.objects.filter(date_fetched=self.latest_rate_date)

    def list(self, request, *args, **kwargs):
        base_currency = request.query_params.get('base', 'USD').upper()
        
        try:
            latest_rate = ExchangeRate.objects.latest('date_fetched')
            self.latest_rate_date = latest_rate.date_fetched

            # Check if we need to update rates
            if timezone.now() >= latest_rate.next_update_time:
                self.update_exchange_rates()
        except ExchangeRate.DoesNotExist:
            # Fetch new rates if no records exist
            self.update_exchange_rates()
            latest_rate = ExchangeRate.objects.latest('date_fetched')
            self.latest_rate_date = latest_rate.date_fetched
        
        queryset = self.get_queryset()
        if base_currency != 'USD':
            usd_to_base_rate = queryset.get(target_currency=base_currency).rate
            if not usd_to_base_rate:
                return Response({"result": "error", "message": f"Base currency {base_currency} not found"}, status=status.HTTP_400_BAD_REQUEST)
            conversion_rates = {rate.target_currency: rate.rate / usd_to_base_rate for rate in queryset}
        else:
            conversion_rates = {rate.target_currency: rate.rate for rate in queryset}

        return Response(conversion_rates, status=status.HTTP_200_OK)

    def update_exchange_rates(self):
        response = requests.get('https://open.er-api.com/v6/latest/USD')
        if response.status_code != 200:
            return Response({"result": "error", "message": "Failed to fetch exchange rates"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = response.json()
        conversion_rates = data['rates']
        last_update_time = timezone.now()
        next_update_time = timezone.make_aware(timezone.datetime.utcfromtimestamp(data['time_next_update_unix']))

        # Update existing rates or create if not exists
        for target_currency, rate in conversion_rates.items():
            obj, created = ExchangeRate.objects.update_or_create(
                target_currency=target_currency,
                defaults={
                    'rate': rate,
                    'date_fetched': last_update_time,
                    'next_update_time': next_update_time
                }
            )